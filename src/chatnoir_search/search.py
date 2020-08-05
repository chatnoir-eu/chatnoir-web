from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


class SimpleSearch:
    _CLIENT = Elasticsearch(settings.ELASTICSEARCH_HOSTS)

    def __init__(self):
        pass

    def search(self, query, indices):
        s = Search(using=SimpleSearch._CLIENT, index=indices) \
            .query('match', warc_trec_id=query)
        return s.execute()
