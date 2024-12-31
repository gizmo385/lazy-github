from os import walk
from typing import Any

from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.backends.protocol import (
    GithubApiBackend,
    GithubApiRequestFailed,
    GithubApiResponse,
    Headers,
    QueryParams,
)
from lazy_github.models.github import User


class OfflineApiResponse(GithubApiResponse):
    def is_success(self) -> bool:
        return False

    def raise_for_status(self) -> None:
        raise GithubApiRequestFailed()

    def json(self) -> Any:
        return {}

    @property
    def text(self) -> str:
        return ""

    @property
    def headers(self) -> dict[str, str]:
        return {}


class OfflineBackend(GithubApiBackend):
    async def get(
        self,
        url: str,
        headers: Headers | None = None,
        params: QueryParams | None = None,
    ) -> Any:
        return OfflineApiResponse()

    async def post(
        self,
        url: str,
        headers: Headers | None = None,
        json: dict[str, str] | None = None,
    ) -> Any:
        return OfflineApiResponse()

    async def patch(
        self,
        url: str,
        headers: Headers | None = None,
        json: dict[str, str] | None = None,
    ) -> Any:
        return OfflineApiResponse()

    async def put(
        self,
        url: str,
        headers: Headers | None = None,
        json: dict[str, str] | None = None,
    ) -> Any:
        return OfflineApiResponse()

    async def get_user(self) -> User:
        response = await self.get("/user")
        return User(**response.json())

    def github_headers(self, accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: int | None = None) -> Headers:
        """Helper function to build a request with specific headers"""
        return {}
