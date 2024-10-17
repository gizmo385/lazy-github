from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.git_cli import current_local_repo_full_name
from lazy_github.lib.github.auth import token
from lazy_github.lib.github.backends.cli import GithubCliClient
from lazy_github.lib.github.backends.http import GithubApiClient
from lazy_github.lib.github.backends.protocol import GithubBackendProtocol
from lazy_github.lib.utils import classproperty
from lazy_github.models.github import Repository


class LazyGithubContext:
    """Globally accessible wrapper class that centralizes access to the configuration and the Github API client"""

    # Attributes exposed via properties
    _config: Config | None = None
    _client: GithubBackendProtocol | None = None
    _current_directory_repo: str | None = None

    # Directly assigned attributes
    access_token: str | None = None
    current_repo: Repository | None = None

    @classproperty
    def config(cls) -> Config:
        if cls._config is None:
            cls._config = Config.load_config()
        return cls._config

    @classproperty
    def client(cls) -> GithubBackendProtocol:
        # Ideally this is would just be a none check but that doesn't properly type check for some reason
        if not isinstance(cls._client, (GithubApiClient, GithubCliClient)):
            # cls._client = GithubApiClient(cls.config, token())
            cls._client = GithubCliClient(cls.config)
        return cls._client

    @classproperty
    def current_directory_repo(cls) -> str | None:
        """The owner/name of the repo associated with the current working directory (if one exists)"""
        if not cls._current_directory_repo:
            cls._current_directory_repo = current_local_repo_full_name()
        return cls._current_directory_repo

    @classmethod
    def _github_headers(cls, accept: str, cache_duration: int | None) -> dict[str, str]:
        """Helper function to build headers for Github API requests"""
        headers = {"Accept": accept, "Authorization": f"Bearer {token()}"}
        max_age = cache_duration or cls.config.cache.default_ttl
        headers["Cache-Control"] = f"max-age={max_age}"
        return headers


def github_headers(accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: int | None = None) -> dict[str, str]:
    """Helper function to build headers for Github API requests"""
    return LazyGithubContext._github_headers(accept, cache_duration)
