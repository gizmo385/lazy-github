from typing import Any, Protocol

from lazy_github.models.github import User


class GithubStatusException(Exception):
    def __init__(self, status: int, source: Exception):
        self.status = status
        self.source = source


class GithubResponse(Protocol):
    """
    This is basically a wrapper around the HTTPX response class to make introducing
    a separate github CLI backend easier.
    """

    def raise_for_status(self) -> None: ...
    def json(self) -> Any: ...


class GithubBackendProtocol(Protocol):
    """
    An abstraction layer around the HTTP functions in Hishel to make supporting a github
    cli backend easier.
    """

    async def user(self) -> User: ...

    async def get(
        self,
        url: str,
        follow_redirects: bool = True,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> GithubResponse: ...

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> GithubResponse: ...

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> GithubResponse: ...
