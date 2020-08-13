import boto3
from botocore.errorfactory import ClientError
from django.conf import settings
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import connections
from warcio.recordloader import ArcWarcRecordLoader
from warcio.bufferedreaders import DecompressingBufferedReader

import logging

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

    def retrieve_by_uuid(self, doc_uuid, doc_index):
        try:
            index = get_index(doc_index)
            doc = index.warc_meta_doc.get(id=doc_uuid)
        except NotFoundError:
            return None

        try:
            obj = self._S3_RESOURCE.Object(index.warc_bucket, doc.warc_file)
            start = doc.warc_offset
            end = start + doc.http_length
            stream = obj.get(Range='bytes={}-{}'.format(start, end))['Body']
        except ClientError:
            logger.error('Document with ID {} found in index {}, but could not in cache'.format(
                doc_uuid, index.interal_name))
            return None

        record = ArcWarcRecordLoader().parse_record_stream(DecompressingBufferedReader(stream))

        return {
            'meta': doc,
            'body': record.content_stream().read()
        }
