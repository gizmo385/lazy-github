from typing import Optional

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.git_cli import current_local_repo_full_name
from lazy_github.lib.github.backends.protocol import BackendType
from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.utils import classproperty
from lazy_github.models.github import Repository


class LazyGithubContext:
    """Globally accessible wrapper class that centralizes access to the configuration and the Github API client"""

    # Attributes exposed via properties
    _config: Config | None = None
    _client: GithubClient | None = None
    _current_directory_repo: str | None = None

    # Directly assigned attributes
    current_repo: Repository | None = None

    @classproperty
    def config(cls) -> Config:
        if cls._config is None:
            cls._config = Config.load_config()
        return cls._config

    @classproperty
    def client_type(cls) -> BackendType:
        return cls.config.api.client_type

    @classproperty
    def client(cls) -> GithubClient:
        # Ideally this is would just be a none check but that doesn't properly type check for some reason
        if not isinstance(cls._client, GithubClient):
            match cls.client_type:
                case BackendType.GITHUB_CLI:
                    cls._client = GithubClient.cli(cls.config)
                case BackendType.RAW_HTTP:
                    from lazy_github.lib.github.auth import get_api_token

                    cls._client = GithubClient.hishel(cls.config, get_api_token())
                case _:
                    raise TypeError(f"Invalid client type in config: {cls.client_type}")
        return cls._client

    @classproperty
    def current_directory_repo(cls) -> str | None:
        """The owner/name of the repo associated with the current working directory (if one exists)"""
        if not cls._current_directory_repo:
            cls._current_directory_repo = current_local_repo_full_name()
        return cls._current_directory_repo


def github_headers(accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None) -> dict[str, str]:
    """Helper function to build headers for Github API requests"""
    return LazyGithubContext.client.github_headers(accept, cache_duration)
