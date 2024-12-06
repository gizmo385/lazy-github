from lazy_github.lib.github.backends.protocol import GithubApiBackend
from lazy_github.lib.github.client import GithubClient


class HishelGithubApiBackend(GithubApiBackend):
    def __init__(self, api_client: GithubClient) -> None:
        self.api_client = api_client

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
    ) -> dict[str, str]:
        response = await self.api_client.get(url, headers=headers, params=query_params)
        response.raise_for_status()
        return response.json()

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ):
        response = await self.api_client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> dict[str, str]:
        response = await self.api_client.patch(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
