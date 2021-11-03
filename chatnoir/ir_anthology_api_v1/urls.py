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

from chatnoir_search_v1 import ir_anthology_search
from chatnoir_api_v1.urls import *
import chatnoir_api_v1.views as views

app_name = 'ir_anthology_api_v1'

# Monkey-patch search backends
views.SimpleSearch = ir_anthology_search.SimpleSearch
views.PhraseSearch = ir_anthology_search.PhraseSearch
