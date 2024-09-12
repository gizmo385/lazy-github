from typing import Optional

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.auth import token
from lazy_github.lib.github.client import GithubClient
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
            cls._client = GithubClient(cls.config, token())
        return cls._client


def github_headers(accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None) -> dict[str, str]:
    """Helper function to build headers for Github API requests"""
    return LazyGithubContext.client.github_headers(accept, cache_duration)
