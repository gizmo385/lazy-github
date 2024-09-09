from collections.abc import Coroutine
from typing import Any, Optional

import hishel
from httpx import URL, Response
from httpx._types import HeaderTypes, QueryParamTypes

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.auth import token
from lazy_github.models.github import User


class GithubClient(hishel.AsyncCacheClient):
    def __init__(self, config: Config, access_token: str) -> None:
        storage = hishel.AsyncFileStorage(base_path=config.cache.cache_directory)
        super().__init__(storage=storage, base_url=config.api.base_url)
        self.config = config
        self.access_token = access_token
        self._user: User | None = None

    def headers_with_auth_accept(
        self, accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None
    ) -> dict[str, str]:
        """Helper function to build a request with specific headers"""
        headers = {"Accept": accept, "Authorization": f"Bearer {self.access_token}"}
        max_age = cache_duration or self.config.cache.default_ttl
        headers["Cache-Control"] = f"max-age={max_age}"
        return headers

    async def user(self) -> User:
        """Returns the authed user for this client"""
        if self._user is None:
            response = await self.get("/user", headers=self.headers_with_auth_accept())
            self._user = User(**response.json())
        return self._user


_GITHUB_CLIENT: GithubClient | None = None


def _get_client() -> GithubClient:
    global _GITHUB_CLIENT
    if not _GITHUB_CLIENT:
        _GITHUB_CLIENT = GithubClient(Config.load_config(), token())
    return _GITHUB_CLIENT


def get(
    url: URL | str,
    headers: HeaderTypes | None = None,
    params: QueryParamTypes | None = None,
    follow_redirects: bool = True,
) -> Coroutine[Any, Any, Response]:
    return _get_client().get(url, headers=headers, params=params, follow_redirects=follow_redirects)


def post(url: URL | str, json: Any | None = None, headers: HeaderTypes | None = None) -> Coroutine[Any, Any, Response]:
    return _get_client().post(url, json=json, headers=headers)


def patch(url: URL | str, json: Any | None, headers: HeaderTypes | None = None) -> Coroutine[Any, Any, Response]:
    return _get_client().patch(url, json=json, headers=headers)


def headers_with_auth_accept(
    accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None
) -> dict[str, str]:
    return _get_client().headers_with_auth_accept(accept, cache_duration)


async def user() -> User:
    return await _get_client().user()
