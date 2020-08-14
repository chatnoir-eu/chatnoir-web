import logging
import os
import urllib.parse as urlparse

import boto3
from botocore.errorfactory import ClientError
from bs4 import BeautifulSoup, NavigableString, Tag
from bs4.formatter import HTMLFormatter
from django.conf import settings
from django.urls import reverse
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import connections, Search
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

    def retrieve_by_uuid(self, doc_index, doc_uuid, basic_html=False):
        """
        Retrieve document by its UUID.

        :param doc_index: index shorthand name
        :param doc_uuid: document UUID
        :param basic_html: parse HTML content to basic "plaintext" HTML subset
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        try:
            index = get_index(doc_index)
            doc = index.warc_meta_doc.get(id=doc_uuid)
        except NotFoundError:
            return None

        return self._read_warc_content(index.warc_bucket, doc_index, doc, basic_html)

    def retrieve_by_filter(self, doc_index, basic_html=False, **filter_expr):
        """
        Retrieve first document that matches the given filter expression in the WARC meta index.

        :param doc_index: index shorthand name
        :param basic_html: parse HTML content to basic "plaintext" HTML subset
        :param filter_expr: term filter expression (e.g. warc_target_uri="http://example.com")
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        index = get_index(doc_index)
        result = (Search()
                  .index(index.warc_index_name)
                  .filter('term', **filter_expr)[:1].execute())

        if not result.hits:
            return None

        return self._read_warc_content(index.warc_bucket, doc_index, result.hits[0], basic_html)

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

    def _read_warc_content(self, warc_bucket, doc_index, doc, basic_html):
        """
        Read and parse WARC content stream.

        :param warc_bucket: S3 bucket name
        :param doc_index: index shorthand name
        :param doc: WARC meta index document
        :param basic_html: parse HTML content to basic "plaintext" HTML subset
        :return: dict(meta=WarcMetaDoc, body=str)
        """
        record = self._read_warc_record(warc_bucket, doc.warc_file, doc.warc_offset, doc.http_length)

        if not record:
            return None

        body = self._rewrite_links(record.content_stream().read(), doc.warc_target_uri, doc_index)
        if basic_html:
            body = BasicHtmlFormatter.format(body)

        return {
            'meta': doc,
            'body': body
        }

    @classmethod
    def _rewrite_links(cls, html_doc, source_url, index):
        """
        Rewrite links in an HTML document.

        Link URIs are rewritten to point to the cache endpoint proxy.
        Images and embeds are replaced with their direct absolute URLs.

        :param html_doc: HTML document as string
        :param source_url: source URL from which this document was crawled for resolving relative paths
        :param index: index containing the document
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

        # Remove base tags
        for base in soup.select('head base'):
            base.decompose()

        return str(soup)

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

    BASIC_HTML_ALLOWED_BLOCK_ELEMENTS = [
        'p', 'pre', 'blockquote',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'dl', 'dt', 'dd', 'li'
    ]

    BASIC_HTML_ALLOWED_INLINE_ELEMENTS = [
        'b', 'i', 'em', 'strong', 'code'
    ]

    BASIC_HTML_BREAK_ELEMENTS = [
        'br', 'tr'
    ]

    BASIC_HTML_COLLAPSE_BREAK_ELEMENTS = [
        'article', 'aside', 'button', 'caption', 'div', 'fieldset', 'figcaption',
        'figure', 'footer', 'form', 'header', 'hgroup', 'output', 'section', 'table'
    ]

    BASIC_HTML_DOUBLE_BREAK_ELEMENTS = [
        'li', 'dt', 'dd'
    ]

    BASIC_HTML_LIST_ELEMENTS = [
        'ul', 'ol', 'dl'
    ]

    BASIC_HTML_LIST_ITEM_ELEMENTS = [
        'li', 'dt'
    ]

    @staticmethod
    def format(html_doc):
        soup = BeautifulSoup(html_doc, 'html.parser')
        body = soup.find('body')
        if not body:
            body = soup

        return body

    @staticmethod
    def _traverse(el):
        for child in el.children:
            yield child
