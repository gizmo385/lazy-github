from typing import Any
import hishel
from httpx import HTTPStatusError, Response

from lazy_github.lib.config import Config
from lazy_github.lib.github.backends.protocol import GithubBackendProtocol, GithubResponse, GithubStatusException
from lazy_github.models.github import User


class HttpGithubClient(hishel.AsyncCacheClient):
    def __init__(self, config: Config, access_token: str) -> None:
        storage = hishel.AsyncFileStorage(base_path=config.cache.cache_directory)
        super().__init__(storage=storage, base_url=config.api.base_url)
        self.config = config
        self.access_token = access_token
        self._user: User | None = None

    async def user(self) -> User:
        """Returns the authed user for this client"""
        auth_header = {"Authorization": f"Bearer {self.access_token}"}
        if self._user is None:
            response = await self.get("/user", headers=auth_header)
            self._user = User(**response.json())
        return self._user


class HttpGithubResponse(GithubResponse):
    def __init__(self, http_response: Response) -> None:
        self.http_response = http_response

    def raise_for_status(self) -> None:
        try:
            self.http_response.raise_for_status()
        except HTTPStatusError as hse:
            raise GithubStatusException(hse.response.status_code, hse)

    @property
    def headers(self) -> dict[str, str]:
        return dict(self.http_response.headers)

    def json(self) -> Any:
        return self.http_response.json()

    @property
    def text(self) -> str:
        return self.http_response.text


class GithubApiClient(GithubBackendProtocol):
    def __init__(self, config: Config, access_token: str) -> None:
        self.client = HttpGithubClient(config, access_token)

    async def user(self) -> User:
        return await self.client.user()

    async def get(
        self,
        url: str,
        follow_redirects: bool = True,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> GithubResponse:
        http_response = await self.client.get(url, follow_redirects=follow_redirects, headers=headers, params=params)
        return HttpGithubResponse(http_response)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any = None,
    ) -> GithubResponse:
        http_response = await self.client.post(url, headers=headers, json=json)
        return HttpGithubResponse(http_response)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any = None,
    ) -> GithubResponse:
        http_response = await self.client.post(url, headers=headers, json=json)
        return HttpGithubResponse(http_response)
