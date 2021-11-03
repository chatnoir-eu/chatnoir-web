import elasticsearch_dsl as edsl
from django.conf import settings
from elasticsearch.exceptions import NotFoundError

_INDICES = {}


def get_index(shorthand):
    if not _INDICES:
        _INDICES.update({k: SearchIndex(k) for k in settings.SEARCH_INDICES})

    return _INDICES.get(shorthand)


class SearchIndex:
    class WarcMetaDocBase(edsl.Document):
        source_file = edsl.Keyword()
        source_offset = edsl.Long()
        content_length = edsl.Long()
        content_type = edsl.Keyword()
        content_encoding = edsl.Keyword()
        http_content_length = edsl.Long()
        http_content_type = edsl.Keyword()
        warc_type = edsl.Keyword()
        warc_date = edsl.Date(format='date_time_no_millis')
        warc_record_id = edsl.Keyword()
        warc_trec_id = edsl.Keyword()
        warc_warcinfo_id = edsl.Keyword()
        warc_concurrent_to = edsl.Keyword()
        warc_truncated = edsl.Keyword()
        warc_ip_address = edsl.Ip()
        warc_target_uri = edsl.Keyword()
        warc_identified_payload_type = edsl.Keyword()
        warc_payload_digest = edsl.Keyword()
        warc_block_digest = edsl.Keyword()

        class Meta:
            dynamic_templates = edsl.MetaField([{
                'additional_warc_headers': {
                    'match_mapping_type': 'string',
                    'match': 'warc_*',
                    'mapping': {
                        'type': 'keyword'
                    }
                }
            }])

    def __init__(self, shorthand):
        if shorthand not in settings.SEARCH_INDICES:
            raise NotFoundError('No such index: {}'.format(shorthand))

        self._conf = settings.SEARCH_INDICES[shorthand]

        self.display_name = self._conf['display_name']
        self.interal_name = self._conf['index']
        self.warc_index_name = self._conf['warc_index']
        self.warc_bucket = self._conf['warc_bucket']
        self.compat_search_versions = self._conf['compat_search_versions']

        self.index = edsl.Index(self.interal_name)

        self.warc_index = edsl.Index(self.warc_index_name)

        @self.warc_index.document
        class WarcMetaDoc(self.WarcMetaDocBase):
            pass

        self.warc_meta_doc = WarcMetaDoc
