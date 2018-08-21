import sys

import requests

from botctl.errors import GatewayError
from botctl.types import PlatformVariable


class Gateway:
    def __init__(self, config):
        self._config = config
        self._environment = config.get_environment()
        self._headers = {
            'Content-Type': 'application/json',
            'Authorization': self._config.get_value(self._environment,
                                                    PlatformVariable.TOKEN),
            'Accept': 'application/json'
        }
        self._configure_host()

    def _request(self, method, endpoint, headers, data, json, fail):
        self._headers.update(headers)
        response = requests.request(
            method,
            self._host + endpoint,
            headers=self._headers,
            data=data,
            json=json
        )

        if (fail, response.ok) == (True, False):
            sys.stderr.write(f'Request failed: {response.status_code}\n'
                             f'Response body: {response.text}\n'
                             f'request body: {response.request.body}')
            raise GatewayError(response)

        return response

    def _configure_host(self):
        self._host = ''

    def delete(self, endpoint, headers={}, data={}, json={}, fail=True):
        return self._request('DELETE', endpoint, headers, data, json, fail)

    def get(self, endpoint, headers={}, data={}, json={}, fail=True):
        return self._request('GET', endpoint, headers, data, json, fail)

    def post(self, endpoint, headers={}, data={}, json={}, fail=True):
        return self._request('POST', endpoint, headers, data, json, fail)

    def put(self, endpoint, headers={}, data={}, json={}, fail=True):
        return self._request('PUT', endpoint, headers, data, json, fail)


class BotCMSGateway(Gateway):
    def _configure_host(self):
        self._host = self._config.get_value(self._environment,
                                            PlatformVariable.CMS) + '/api/v1'
