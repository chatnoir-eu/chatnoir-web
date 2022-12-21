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

from django.utils.translation import gettext as _

import chatnoir_search.serp as chatnoir_serp
from chatnoir_search.types import FieldName, minimal, extended, explanation


# Legacy field name pattern
_pattern = '{field}_lang.{lang}'


# noinspection DuplicatedCode
class SerpContext(chatnoir_serp.SerpContext):

    @property
    def results(self):

        results = []
        for hit in self.response.hits:
            full_text_field = FieldName('full_text', pattern=_pattern).i18n(self.search.search_language)
            abstract_field = FieldName('abstract', pattern=_pattern).i18n(self.search.search_language)

            snippet = self.search.get_snippet(hit, [full_text_field, abstract_field], 200)

            title_field = FieldName('title', pattern=_pattern).i18n(self.search.search_language)
            title = self.search.get_snippet(hit, [title_field], 60)
            if not title:
                title = _('[ no title available ]')

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
