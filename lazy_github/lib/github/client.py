import httpx

from lazy_github.lib.config import Config
from lazy_github.lib.github.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.models.core import User


class GithubClient(httpx.AsyncClient):
    def __init__(self, config: Config, access_token: str) -> None:
        super().__init__(base_url=config.api.base_url)
        self.config = config
        self.access_token = access_token
        self._user: User | None = None

    def headers_with_auth_accept(self, accept: str = JSON_CONTENT_ACCEPT_TYPE) -> dict[str, str]:
        """Helper function to build a request with specific headers"""
        return {"Accept": accept, "Authorization": f"Bearer {self.access_token}"}

    async def user(self) -> User:
        """Returns the authed user for this client"""
        if self._user is None:
            response = await self.get("/user", headers=self.headers_with_auth_accept())
            self._user = User(**response.json())
        return self._user
