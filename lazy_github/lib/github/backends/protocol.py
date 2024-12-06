from typing import Protocol


class GithubApiBackend(Protocol):
    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
    ) -> dict[str, str]: ...

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> dict[str, str]: ...

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> dict[str, str]: ...
