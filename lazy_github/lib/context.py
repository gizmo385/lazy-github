from logging.handlers import RotatingFileHandler
from typing import Optional

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.git_cli import current_local_branch_name, current_local_repo_full_name
from lazy_github.lib.github.backends.protocol import BackendType
from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.logging import LazyGithubLogFormatter, lg
from lazy_github.models.github import Repository


class _LazyGithubContext:
    """Globally accessible wrapper class that centralizes access to the configuration and the Github API client"""

    # Attributes exposed via properties
    _config: Config | None = None
    _client: GithubClient | None = None
    _current_directory_repo: str | None = None
    _current_directory_branch: str | None = None
    offline_mode: bool = False

    # Directly assigned attributes
    current_repo: Repository | None = None

    def _setup_logging_handler(self, config: Config) -> None:
        """Setup the file logger for LazyGithub"""
        try:
            config.core.logfile_path.parent.mkdir(parents=True, exist_ok=True)
            lg_file_handler = RotatingFileHandler(
                filename=config.core.logfile_path,
                maxBytes=config.core.logfile_max_bytes,
                backupCount=config.core.logfile_count,
            )
            lg_file_handler.setFormatter(LazyGithubLogFormatter())
            lg.addHandler(lg_file_handler)
        except Exception:
            lg.exception("Failed to setup file logger for LazyGithub")

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = Config.load_config()
            self._setup_logging_handler(self._config)
        return self._config

    @property
    def client_type(self) -> BackendType:
        return self.config.api.client_type

    @property
    def client(self) -> GithubClient:
        # Ideally this is would just be a none check but that doesn't properly type check for some reason
        if not isinstance(self._client, GithubClient):
            match self.client_type:
                case BackendType.GITHUB_CLI:
                    self._client = GithubClient.cli(self.config, self.offline_mode)
                case BackendType.RAW_HTTP:
                    from lazy_github.lib.github.auth import get_api_token

                    self._client = GithubClient.hishel(self.config, get_api_token(), self.offline_mode)
        return self._client

    @property
    def current_directory_repo(self) -> str | None:
        """The owner/name of the repo associated with the current working directory (if one exists)"""
        if not self._current_directory_repo:
            self._current_directory_repo = current_local_repo_full_name()
        return self._current_directory_repo

    @property
    def current_directory_branch(self) -> str | None:
        """The owner/name of the repo associated with the current working directory (if one exists)"""
        if not self._current_directory_branch:
            self._current_directory_branch = current_local_branch_name()
        return self._current_directory_branch


LazyGithubContext = _LazyGithubContext()


def github_headers(accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: Optional[int] = None) -> dict[str, str]:
    """Helper function to build headers for Github API requests"""
    return LazyGithubContext.client.github_headers(accept, cache_duration)
