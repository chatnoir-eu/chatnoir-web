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

from urllib.parse import quote_plus
import uuid

import chatnoir_search_v1.serp as chatnoir_serp
from chatnoir_search_v1.serp import minimal, extended, explanation


# noinspection DuplicatedCode
class SerpContext(chatnoir_serp.SerpContext):

    @property
    def hits(self):
        results = []
        for hit in self.response.hits:
            full_text_key = 'full_text_lang.' + self.search.search_language
            abstract_key = 'abstract_lang.' + self.search.search_language

            snippet = self.search.get_snippet(hit, [full_text_key, abstract_key], 200)

            title_key = 'title_lang.' + self.search.search_language
            title = self.search.get_snippet(hit, [title_key], 60)
            if not title:
                title = '[ no title available ]'

            result_index = self._index_name_to_shorthand(hit.meta.index)

            expl = None
            if hasattr(hit.meta, 'explanation'):
                expl = hit.meta.explanation.to_dict()

            result = {
                'score': minimal(hit.meta.score),
                'index': minimal(result_index),
                'uuid': minimal(uuid.uuid5(uuid.NAMESPACE_URL, 'ir-anthology:' + hit.meta.id)),
                'internal_uri': minimal(f'https://ir.webis.de/anthology/{quote_plus(hit.meta.id)}/'),
                'external_uri': minimal(f'https://doi.org/{getattr(hit, "doi")}'
                                        if hasattr(hit, 'doi') else getattr(hit, 'url', None)),
                'authors': extended(list(getattr(hit, 'authors', []))),
                'doi': minimal(getattr(hit, 'doi', None)),
                'anthology_id': minimal(hit.meta.id),
                'venue': extended(getattr(hit, 'venue', None)),
                'year': extended(getattr(hit, 'year', None)),
                'title': minimal(title),
                'snippet': extended(snippet),
                'explanation': explanation(expl)
            }

            results.append(result)

        return results
