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

import json
from typing import Any, Dict, Optional
from urllib import error, parse, request


class ApiRequest:
    """
    ChatNoir API request abstraction clss.
    """
    def __init__(self, apikey: str, module: str, action: str = None):
        """
        :param module: API key
        :param module:  API module
        :param action: API module action
        """
        self._apikey = apikey
        self._module = module
        self._action = action
        self._error = None

    @property
    def error(self) -> error.HTTPError:
        """
        :return: last HTTP error
        """
        return self._error

    def request(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform API request.

        :param body: API request body
        :return: API response or None in case of an error
        """
        action = '/' + parse.quote(self._action) if self._action else ''
        try:
            payload = json.dumps(body).encode('utf-8')
            req = request.Request('https://www.chatnoir.eu/api/v1/{0}{1}?apikey={2}'.format(
                parse.quote(self._module), action, parse.quote(self._apikey)), data=payload)
            req.add_header('Content-Type', 'application/json')

            content = request.urlopen(req).read()
            if type(content) is bytes:
                content = content.decode('utf-8')
            return json.loads(content)
        except error.HTTPError as e:
            self._error = e
            return None
