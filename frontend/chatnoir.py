import json
from typing import Any, Dict, Optional
from urllib import error, request, parse


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
