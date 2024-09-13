from typing import Optional

import hishel

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.models.github import User


class GithubClient(hishel.AsyncCacheClient):
    def __init__(self, config: Config, access_token: str) -> None:
        storage = hishel.AsyncFileStorage(base_path=config.cache.cache_directory)
        super().__init__(storage=storage, base_url=config.api.base_url)
        self.config = config
        self.access_token = access_token
        self._user: User | None = None

    def github_headers(
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
            response = await self.get("/user", headers=self.github_headers())
            self._user = User(**response.json())
        return self._user
