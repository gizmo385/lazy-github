from typing import Optional

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.client import GithubClient, _get_client
from lazy_github.lib.utils import classproperty


class LazyGithubContext:
    """Globally accessible wrapper class that centralizes access to the configuration and the Github API client"""

    _config: Config | None = None
    _client: GithubClient | None = None

    @classproperty
    def config(cls) -> Config:
        if cls._config is None:
            cls._config = Config.load_config()
        return cls._config

    @classproperty
    def client(cls) -> GithubClient:
        # Ideally this is would just be a none check but that doesn't properly type check for some reason
        if not isinstance(cls._client, GithubClient):
            cls._client = _get_client(config=cls.config)
        return cls._client


def github_headers(accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None) -> dict[str, str]:
    """Helper function to build headers for Github API requests"""
    headers = {"Accept": accept, "Authorization": f"Bearer {LazyGithubContext.client.access_token}"}
    max_age = cache_duration or LazyGithubContext.config.cache.default_ttl
    headers["Cache-Control"] = f"max-age={max_age}"
    return headers
