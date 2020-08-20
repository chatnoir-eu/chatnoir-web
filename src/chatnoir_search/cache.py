import logging
import os
import re
import urllib.parse as urlparse

import boto3
from botocore.errorfactory import ClientError
import bleach
from bs4 import BeautifulSoup, Tag
from django.conf import settings
from django.urls import reverse
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import connections, Search
import html
from warcio.bufferedreaders import DecompressingBufferedReader
from warcio.recordloader import ArcWarcRecordLoader

from .es_util import get_index

logger = logging.getLogger(__name__)


class CacheDocument:
    _S3_RESOURCE = None

    def __init__(self):
        self.warc_record = None

        if 'default' not in connections.connections._conns:
            connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

        self._init_s3()

    def _init_s3(self):
        if self._S3_RESOURCE is None:
            self._S3_RESOURCE = boto3.resource('s3', **settings.S3_ENDPOINT_PROPERTIES)

    def retrieve_by_uuid(self, doc_index, doc_uuid):
        """
        Retrieve document by its UUID.

        :param doc_index: index shorthand name
        :param doc_uuid: document UUID
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        try:
            index = get_index(doc_index)
            doc = index.warc_meta_doc.get(id=doc_uuid)
        except NotFoundError:
            return None

        return self._read_warc_content(index.warc_bucket, doc_index, doc)

    def retrieve_by_filter(self, doc_index, **filter_expr):
        """
        Retrieve first document that matches the given filter expression in the WARC meta index.

        :param doc_index: index shorthand name
        :param filter_expr: term filter expression (e.g. warc_target_uri="http://example.com")
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        index = get_index(doc_index)
        result = (Search().doc_type(index.warc_meta_doc)
                  .index(index.warc_index_name)
                  .filter('term', **filter_expr)[:1].execute())

        if not result.hits:
            return None

        return self._read_warc_content(index.warc_bucket, doc_index, result.hits[0])

    def _read_warc_record(self, warc_bucket, warc_file, start_offset, record_size):
        """
        Read WARC record from S3 object store.

        :param warc_bucket: S3 bucket
        :param warc_file: S3 object name
        :param start_offset: byte offset of record in WARC file
        :param record_size: length of record in bytes
        :return: ArcWarcRecord
        """
        try:
            obj = self._S3_RESOURCE.Object(warc_bucket, warc_file)
            start = start_offset
            end = start + record_size
            stream = obj.get(Range='bytes={}-{}'.format(start, end))['Body']
            return ArcWarcRecordLoader().parse_record_stream(DecompressingBufferedReader(stream))

        except ClientError:
            return None

    def _read_warc_content(self, warc_bucket, doc_index, doc):
        """
        Read and parse WARC content stream.

        :param warc_bucket: S3 bucket name
        :param doc_index: index shorthand name
        :param doc: WARC meta index document
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        record = self._read_warc_record(warc_bucket, doc.source_file, doc.source_offset, doc.http_content_length)

        if not record:
            return None

        body = record.content_stream().read()
        if doc.http_content_type:
            if doc.http_content_type.startswith('text/') or \
                    doc.http_content_type in ('application/json', 'application/xhtml+xml'):
                body = body.decode(doc.content_encoding, errors='replace')

            if doc.http_content_type in ('text/html', 'application/xhtml+xml'):
                body = self._post_process_html(body, doc.warc_target_uri, doc_index,
                                               doc.http_content_type == 'application/xhtml+xml')

        # ClueWeb09 messed up the encoding of many pages, so strip Unicode replacement characters
        if doc.warc_trec_id and doc.warc_trec_id.startswith('clueweb09'):
            body = body.replace('\ufffd', '')

        return {
            'meta': doc,
            'body': body
        }

    @classmethod
    def _post_process_html(cls, html_doc, source_url, index, xhtml_mode=False):
        """
        Post-process HTML by rewriting links in an HTML document and updating encoding information.

        Link URIs are rewritten to point to the cache endpoint proxy.
        Images and embeds are replaced with their direct absolute URLs.

        :param html_doc: HTML document as string
        :param source_url: source URL from which this document was crawled for resolving relative paths
        :param index: index containing the document
        :param xhtml_mode: return XHTML-compatible document
        :return: modified HTML
        """

        link_base = reverse('search:cache') + '?index={}&raw&url='.format(urlparse.quote(index))

        soup = BeautifulSoup(html_doc, 'html.parser')
        for a in soup.select('a[href], area[href]'):
            a['href'] = link_base + urlparse.quote(cls._get_absolute_uri(a['href'], source_url))

        for link in soup.select('link[href]'):
            link['href'] = cls._get_absolute_uri(link['href'], source_url)

        for embed in soup.select('img[src], script[src], iframe[src], video[src], audio[src], input[type=image][src]'):
            embed['src'] = cls._get_absolute_uri(embed['src'], source_url)

        for obj in soup.select('object[data]'):
            obj['data'] = cls._get_absolute_uri(obj['data'], source_url)

        # Add HTML head elements (find or create head first)
        head = soup.find('head')
        if not head:
            head = soup.new_tag('head')
            head_insert = soup.find('html')
            if head_insert:
                head_insert.insert(0, head)
            else:
                soup.find().insert_before(head)

        # Remove existing robots meta and base tags
        [e.decompose() for e in list(head.select('meta[name="robots" i], base'))]

        # Insert robots no-index, nofollow
        no_index = soup.new_tag('meta')
        no_index['name'] = 'robots'
        no_index['content'] = 'noindex, nofollow'
        head.insert(0, no_index)

        # Set encoding to UTF-8
        meta_enc = head.select('meta[charset]')
        for e in meta_enc:
            e['charset'] = 'utf-8'

        meta_enc = head.select('meta[http-equiv="Content-Type" i]')
        for e in meta_enc:
            e['content'] = re.sub(r'charset=[\w-]+', 'charset=utf-8', e['content'])

        return soup.encode(formatter='minimal' if xhtml_mode else 'html5').decode('utf-8')

    @classmethod
    def _get_absolute_uri(cls, relative_url, base_url):
        """
        Resolve a relative URI to an absolute URI.
        If `relative_url` is already absolute (i.e. with schema and network location), it's returned unchanged.

        :param relative_url: relative URI
        :param base_url: absolute base URL for resolving `relative_url`
        :return: absolute URI
        """

        url_parts = urlparse.urlparse(relative_url)
        if url_parts.scheme and url_parts.netloc:
            return relative_url

        base_url_parts = urlparse.urlparse(base_url)
        repl = {}
        if not url_parts.scheme:
            repl['scheme'] = base_url_parts.scheme

        if not url_parts.netloc:
            repl['netloc'] = base_url_parts.netloc

        if not url_parts.path.startswith('/'):
            base_path = base_url_parts.path
            if not base_path.endswith('/'):
                base_path = os.path.dirname(base_path)
            repl['path'] = os.path.abspath(os.path.join(base_path, url_parts.path))

        return urlparse.urlunparse(url_parts._replace(**repl))


class BasicHtmlFormatter:
    """
    Formatter for creating basic "plaintext" HTML.
    """

    ALLOWED_ELEMENTS = [
        'p', 'div', 'pre', 'main', 'nav', 'section', 'article', 'header', 'footer', 'blockquote', 'aside', 'details',
        'hgroup', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'dl', 'dt', 'dd', 'li',
        'a', 'b', 'i', 'em', 'strong', 'code',
        'br', 'hr'
    ]

    ALLOWED_ATTRS = {
        'a': ['href']
    }

    ALLOWED_PROTOCOLS = [
        'http',
        'https'
    ]

    @classmethod
    def format(cls, html_doc):
        soup = BeautifulSoup(html_doc, 'html.parser')

        title = soup.find('title')
        if title:
            title = ''.join(('<title>', html.escape(title.text), '</title>'))
        else:
            title = '<title>Cache Result</title>'

        head = soup.find('head')
        if head:
            head.decompose()

        # Remove non-content elements
        for el in list(soup.select('script, style')):
            el.decompose()

        # Replace disallowed block elements with divs
        for tr in soup.select('table, tr, dialog, fieldset, form, figure'):
            tr.name = 'div'

        bleached_html = bleach.clean(str(soup),
                                     tags=cls.ALLOWED_ELEMENTS,
                                     attributes=cls.ALLOWED_ATTRS,
                                     protocols=cls.ALLOWED_PROTOCOLS,
                                     strip=True,
                                     strip_comments=True)

        # Post-process bleached HTML
        bleached_soup = BeautifulSoup('\n'.join(('<body>', bleached_html, '</body>')), 'html.parser')

        # Strip tags with no content
        decompose = []
        for el in bleached_soup.descendants:
            if isinstance(el, Tag) and el.name not in ('br', 'td', 'th') and not el.get_text(strip=True):
                decompose.append(el)
        [d.decompose() for d in decompose]

        return '\n'.join(
            ('<!doctype html>',
             '<head>',
             '<meta charset="utf-8">',
             '<meta name="robots" content="noindex, nofollow">',
             '<meta name="generator" content="The ChatNoir search engine - www.chatnoir.eu">',
             title,
             '</head>',
             bleached_soup.prettify(formatter="html5"))
        )
