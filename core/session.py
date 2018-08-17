# aiohttp3 patching
# https://github.com/Fahreeve/aiovk/issues/30
from urllib.parse import parse_qs

import aiohttp

from aiovk import ImplicitSession as BaseImplicitSession, TokenSession as BaseTokenSession
from aiovk.drivers import HttpDriver


class FairDriver(HttpDriver):
    async def post_text(self, url, data, timeout=None):
        async with self.session.post(url, data=data, timeout=timeout or self.timeout) as response:
            fragment = parse_qs(response.real_url.fragment)
            [access_token] = fragment.get('access_token', [None])
            url = response.url.update_query(access_token=access_token) if access_token else response.url
            return url, await response.text()


def _get_driver():
    session = aiohttp.ClientSession()
    return FairDriver(session=session)


class ApiVersionMixin:
    API_VERSION = '5.80'


class ImplicitSession(ApiVersionMixin, BaseImplicitSession):
    def __init__(self, login: str, password: str, app_id: int, scope: str or int or list = None,
                 timeout: int = 10, num_of_attempts: int = 5, driver=None):
        super().__init__(login, password, app_id, scope, timeout, num_of_attempts, _get_driver())


class TokenSession(ApiVersionMixin, BaseTokenSession):
    def __init__(self, access_token: str = None, timeout: int = 10):
        super().__init__(access_token, timeout, _get_driver())
