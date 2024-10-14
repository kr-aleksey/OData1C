from typing import Any
from urllib.parse import quote, urlencode

import requests
import requests.auth as auth
import requests.exceptions as r_exceptions

from OData.exeptions import ClientConnectionError


class Connection:

    def __init__(self,
                 host: str,
                 protocol: str,
                 authentication: auth.AuthBase,
                 connection_timeout: int | float = 10,
                 read_timeout: int | float = 121) -> None:
        self.base_url = f'{protocol}://{host}/'
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.auth = authentication
        self.headers = {
            # 'Content-Type': 'application/json',
            'Accept': 'application/json',
            # 'Connection': 'keep-alive'
        }
        self.session = None

    def __enter__(self) -> 'Connection':
        self.session = self._create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = self.auth
        session.headers.update(self.headers)
        return session

    def get_url(self,
                relative_url: str,
                query_params: dict[str, Any] | None = None) -> str:
        url = f'{self.base_url}{relative_url}'
        if query_params:
            url = f'{url}?{urlencode(query_params, quote_via=quote)}'
        return url

    def request(self,
                method: str,
                relative_url: str,
                query_params: dict[str, Any] | None = None,
                data: dict[str, Any] | None = None) -> requests.Response:
        if self.session is None:
            session = self._create_session()
        else:
            session = self.session
        url = self.get_url(relative_url, query_params)
        req = requests.Request(method=method, url=url, json=data)
        prepared = session.prepare_request(req)
        try:
            response: requests.Response = session.send(
                prepared,
                timeout=(self.connection_timeout, self.read_timeout)
            )
        except (r_exceptions.ConnectionError, r_exceptions.Timeout):
            raise ClientConnectionError
        finally:
            if self.session is None:
                session.close()
        return response
