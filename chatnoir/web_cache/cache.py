# Copyright 2021 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import re
import urllib.parse as urlparse

import boto3
from botocore.errorfactory import ClientError
from django.conf import settings
from django.utils .html import escape as html_escape
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import connections, Search
from fastwarc import ArchiveIterator
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.encoding import bytes_to_str
from resiliparse.parse.html import HTMLTree
import json

logger = logging.getLogger(__name__)


class CacheDocument:
    _S3_RESOURCE = None

    def __init__(self):
        self._warc_record = None
        self._meta_doc = None
        self._doc_index = None
        self._doc_bytes = None
        self._html_tree = None
        self._is_clueweb09 = False   # ClueWeb09 quirks mode
        self._doc_found = False
        self._raw_doc_content_type = 'application/octet-stream'

        if 'default' not in connections.connections._conns:
            connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

        self._init_s3()

    def _init_s3(self):
        if self._S3_RESOURCE is None:
            self._S3_RESOURCE = boto3.resource('s3', **settings.S3_ENDPOINT_PROPERTIES)

    def retrieve_by_idx_id(self, index, idx_uuid):
        """
        Retrieve document by its UUID.

        :param index: index object
        :param idx_uuid: document internal index UUID
        :return: True on success
        """
        try:
            doc = index.warc_meta_doc.get(id=idx_uuid)
        except NotFoundError:
            return False

        self._doc_index = index
        self._meta_doc = doc

        return self._read_record(doc)

    def _read_record(self, doc):
        """
        read the record encoded by the document doc. If the source_file of doc points to a json(lines) file, the record is parsed as jsonl, otherwise as warc.

        :param doc: The document with source_file and source_offset
        :return: True on success, else an exception is thrown
        """
        if doc.source_file.endswith('.json') or doc.source_file.endswith('.jsonl'):
            self._read_jsonl_record(doc.source_file, doc.source_offset, doc.content_length)
        else:
            self._read_warc_record(doc.source_file, doc.source_offset)

        return True

    def retrieve_by_filter(self, index, **filter_expr):
        """
        Retrieve first document that matches the given filter expression in the WARC meta index.

        :param index: index object
        :param filter_expr: term filter expression (e.g. warc_target_uri="https://example.com")
        :return: True on success
        """
        result = (Search().doc_type(index.warc_meta_doc)
                  .index(index.warc_index_name)
                  .filter('term', **filter_expr)
                  .extra(terminate_after=1).execute())

        if not result.hits:
            return False

        doc = result.hits[0]
        self._doc_index = index
        self._meta_doc = doc
        return self._read_record(doc)

    def _read_jsonl_record(self, jsonl_file_url, start_offset, content_length=None):
        """
        Read a jsonl line from S3 object store.

        :param jsonl_file_url: S3 object URL
        :param start_offset: byte offset of record in WARC file
        """
        if not jsonl_file_url.startswith('s3://'):
            raise ValueError('JSONL URL is not an S3 URL.')

        if not jsonl_file_url.endswith('.json') and not jsonl_file_url.endswith('.jsonl'):
            raise ValueError('JSONL URL does not point to json file.')

        if not content_length or content_length < 10:
            content_length = 10*102400

        try:
            bucket_name, obj_name = jsonl_file_url[5:].split('/', 1)
            obj = self._S3_RESOURCE.Object(bucket_name, obj_name)
            start = start_offset
            end = start_offset + content_length
            stream = obj.get(Range=f'bytes={start}-{end}')['Body']
            response = stream._raw_stream.read().decode()
            response = response.split('\n')[0].strip()
            response = json.loads(response)
            self._meta_doc.http_content_type = 'text/plain'
            self._doc_bytes = json.dumps(response, indent=4).encode()
            self._doc_found = True

            title = None
            if 'title' in response:
                title = response['title']
            elif 'original_document' in response and 'title' in response['original_document']:
                title = response['original_document']['title']
            elif 'docid' in response:
                title = f'Document {response["docid"]}'
            elif 'docno' in response:
                title = f'Document {response["docno"]}'

            body = f'<h1>{html_escape(title)}</h1>'

            if 'headings' in response:
                body += f'<h2>Headings:</h2><p>' + html_escape(response['headings']) + '</p>'

            if 'original_document' in response and 'headings' in response['original_document']:
                body += f'<h2>Headings:</h2><p>' + html_escape(response['original_document']['headings']) + '</p>'

            if 'segment' in response:
                body += '<h2>Segment (from the page):</h2><p>' + html_escape(response['segment']) + '</p>'

            if 'body' in response:
                body += '<h2>Body (from the page):</h2><p>' + html_escape(response['body']) + '</p>'

            if 'text' in response:
                body += '<h2>Text:</h2><p>' + html_escape(response['text']) + '</p>'

            body = body.replace('\n', '<br>')
            html = ''.join(['<html><head><title>', html_escape(title), '</title></head><body>', body, '</body></html>'])

            self._html_tree = HTMLTree.parse(html)
            self._raw_doc_content_type = 'application/json'

        except Exception as e:
            logger.error('Could not parse json record.', e)
            raise ValueError('Could not parse json record', e)

    def _read_warc_record(self, warc_file_url, start_offset):
        """
        Read WARC record from S3 object store.

        :param warc_file_url: S3 object URL
        :param start_offset: byte offset of record in WARC file
        :return: WarcRecord
        """
        if not warc_file_url.startswith('s3://'):
            raise ValueError('WARC URL is not an S3 URL.')

        # ClueWeb09 WARCs are broken and need further processing
        self._is_clueweb09 = getattr(self._meta_doc, 'warc_trec_id', '').startswith('clueweb09')

        try:
            bucket_name, obj_name = warc_file_url[5:].split('/', 1)
            obj = self._S3_RESOURCE.Object(bucket_name, obj_name)
            start = start_offset
            stream = obj.get(Range=f'bytes={start}-')['Body']
            # Override HTTP parsing flag from meta index to work around broken ClueWeb22 headers
            parse_http = (self._meta_doc.warc_type in ('request', 'response')
                          and self._meta_doc.content_type.startswith('application/http'))
            self._warc_record = next(
                ArchiveIterator(
                    stream._raw_stream,
                    strict_mode=not self._is_clueweb09,
                    parse_http=parse_http
                )
            )
            self._doc_bytes = self._warc_record.reader.read()
            stream.close()
            self._doc_found = True

            self._html_tree = None
            if self._meta_doc.http_content_type and self._meta_doc.http_content_type in (
                    'text/html', 'application/xhtml+xml'):
                self._html_tree = HTMLTree.parse_from_bytes(self._doc_bytes, self._meta_doc.content_encoding)
                self._raw_doc_content_type = 'text/html'
            elif self._meta_doc.http_content_type and self._meta_doc.http_content_type.endswith('/json'):
                self._meta_doc.http_content_type = 'application/json'
            elif self._meta_doc.http_content_type:
                self._raw_doc_content_type = self._meta_doc.http_content_type

        except StopIteration:
            logger.error('End of WARC reached when trying to read position %s.', start_offset)
        except ClientError as e:
            logger.exception(e)

    def _read_doc_content(self, raw_html=False, main_content=False, minimal_html=False):
        """
        Read and parse WARC content stream.

        :param raw_html: do not post-process HTML (i.e., do not rewrite links etc.)
        :param main_content: return only textual main content with minimal HTML formatting
        :param minimal_html: use minimal HTML formatting for main content extraction
        :return: body as string or bytes
        """
        if not self._doc_found:
            logger.warning('Document %s not found in %s.', self._meta_doc.meta.id, self._meta_doc.source_file)
            return None

        body = self._doc_bytes
        if self._html_tree:
            if main_content:
                body = extract_plain_text(self._html_tree, preserve_formatting='minimal_html' if minimal_html else True,
                                          main_content=True, alt_texts=True)
            elif not raw_html:
                body = self._post_process_html(self._html_tree)

            # ClueWeb09 messed up the encoding of many pages, so strip Unicode replacement characters
            if self._is_clueweb09:
                body = (body.replace('\ufffd', '')
                        if type(body) is str else body.replace(b'\xef\xbf\xbd', b''))

            return body

        return bytes_to_str(body, self._meta_doc.content_encoding)

    def raw_doc_content_type(self):
        return self._raw_doc_content_type

    def is_text(self):
        """Document is a plaintext document."""
        return self._meta_doc and not self.is_html() and self._raw_doc_content_type.startswith('text/')

    def is_html(self):
        """Document is a full HTML web page."""
        return self._meta_doc and self._raw_doc_content_type == 'text/html'

    def is_html_fragment(self):
        """Document is an HTML fragment (MS MARCO etc.)."""
        return not self.is_html() and self._html_tree

    def is_json(self):
        """Document is JSON."""
        return self._meta_doc and self._raw_doc_content_type == 'application/json'

    def is_xml(self):
        """Document is XML."""
        return self._meta_doc and (self._raw_doc_content_type == 'text/xml' or
                                   self._raw_doc_content_type.startswith('application/xml'))

    def is_binary(self):
        """Document is not a text document."""
        return not self.is_text() and not self.is_html() and not self.is_json() and not self.is_xml()

    def doc_meta(self):
        """
        :return: WARC document meta information
        """
        return self._meta_doc

    def html(self, post_process=True):
        """
        :param post_process: post-process HTML, i.e., rewrite links etc.
        :return: body as HTML string or bytes (if document is not an HTML document)
        """
        return self._read_doc_content(raw_html=not post_process)

    def bytes(self):
        """
        :return: document as raw bytes
        """
        return self._doc_bytes or b''

    def main_content(self, minimal_html=False):
        """
        :return: extracted main content as string or bytes (if document is not an HTML document)
        """
        return self._read_doc_content(main_content=True, minimal_html=minimal_html)

    def html_title(self):
        if not self._html_tree:
            return ''
        return self._html_tree.title

    def html_meta_viewport(self):
        if not self._html_tree:
            return None
        el = self._html_tree.head.query_selector('meta[name="viewport"]')
        if not el:
            return None
        return el.getattr('content')

    def _post_process_html(self, html_tree):
        """
        Post-process HTML by rewriting links in an HTML document and updating encoding information.

        Link URIs are rewritten to point to the cache endpoint proxy.
        Images and embeds are replaced with their direct absolute URLs.

        :param html_tree: Resiliparse HTML tree
        :return: modified HTML
        """
        if not html_tree.body:
            return ''

        for a in html_tree.body.query_selector_all('a[href], area[href]'):
            a['href'] = self._rewrite_url(a['href'], self._meta_doc.warc_target_uri, False)

        for link in html_tree.body.query_selector_all('link[href]'):
            link['href'] = self._rewrite_url(link['href'], self._meta_doc.warc_target_uri, True)

        for embed in html_tree.body.query_selector_all(
                'img[src], script[src], iframe[src], video[src], audio[src], input[type=image][src]'):
            embed['src'] = self._rewrite_url(embed['src'], self._meta_doc.warc_target_uri, True)

        for obj in html_tree.body.query_selector_all('object[data]'):
            obj['data'] = self._rewrite_url(obj['data'], self._meta_doc.warc_target_uri, True)

        # Add HTML head elements (find or create head first)
        head = html_tree.head
        if not head:
            head = html_tree.document.insert_before(head, html_tree.body)

        # Remove existing robots meta and base tags
        [e.decompose() for e in list(head.query_selector_all('meta[name="robots"], base'))]

        # Insert robots no-index, nofollow
        no_index = html_tree.create_element('meta')
        no_index['name'] = 'robots'
        no_index['content'] = 'noindex, nofollow'
        if head.first_child:
            html_tree.head.insert_before(no_index, head.first_child)
        else:
            head.append_child(no_index)

        # Set encoding to UTF-8
        meta_enc = head.query_selector('meta[charset]')
        if meta_enc:
            meta_enc['charset'] = 'utf-8'

        meta_enc = head.query_selector('meta[http-equiv="Content-Type"]')
        if meta_enc:
            meta_enc['content'] = re.sub(r'charset=[\w-]+', 'charset=utf-8', meta_enc['content'])

        return html_tree.document.html

    def _rewrite_url(self, input_url, source_base, raw=False):
        """
        Resolve a relative URI to an absolute URI.
        If `relative_url` is already absolute (i.e. with schema and network location), it's returned unchanged.

        :param input_url: relative URI
        :param source_base: absolute source base URL for resolving `relative_url`
        :param raw: add "raw" parameter to rewritten URL
        :return: rewritten URI
        """

        input_url = input_url.strip()

        # Return relative fragment URLs as is
        if input_url.startswith('#'):
            return input_url

        # Turn effectively relative fragment URLs into actual fragments
        if input_url.startswith(source_base) and input_url[len(source_base):].startswith('#'):
            return input_url[len(source_base):]

        base_url_parts = urlparse.urlparse(source_base)
        target_url_parts = urlparse.urlparse(input_url)
        repl = {}
        if not target_url_parts.scheme:
            repl['scheme'] = base_url_parts.scheme
        elif target_url_parts.scheme not in ['https', 'http']:
            # Do not rewrite unsafe protocol prefixes
            return input_url

        if not target_url_parts.netloc:
            repl['netloc'] = base_url_parts.netloc

        if not target_url_parts.path.startswith('/'):
            base_path = base_url_parts.path
            if not base_path.endswith('/'):
                base_path = os.path.dirname(base_path)
            repl['path'] = os.path.abspath(os.path.join(base_path, target_url_parts.path))

        new_url = urlparse.urlunparse(target_url_parts._replace(**repl))
        new_url = f'{settings.CACHE_FRONTEND_URL}?index={self._doc_index.shorthand_name}&url={urlparse.quote(new_url)}'
        if raw:
            new_url += '&raw'
        return new_url
