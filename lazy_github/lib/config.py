import json
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Generator, List, Literal, Self

from pydantic import BaseModel, Field

from lazy_github.lib.constants import CONFIG_FOLDER

_CONFIG_FILE_LOCATION = CONFIG_FOLDER / "config.json"

ISSUE_STATE_FILTER = Literal["all"] | Literal["open"] | Literal["closed"]
ISSUE_OWNER_FILTER = Literal["mine"] | Literal["all"]


class ApiConfig(BaseModel):
    base_url: str = "https://api.github.com"


class PullRequestSettings(BaseModel):
    """Changes how PRs are retrieved from the Github API"""

    state_filter: ISSUE_STATE_FILTER = "all"
    owner_filter: ISSUE_OWNER_FILTER = "all"


class IssueSettings(BaseModel):
    """Changes how issues are retrieved from the Github API"""

    state_filter: ISSUE_STATE_FILTER = "all"
    owner_filter: ISSUE_OWNER_FILTER = "all"


class RepositorySettings(BaseModel):
    favorites: List[str] = []


class CacheSettings(BaseModel):
    cache_directory: Path = CONFIG_FOLDER / ".cache"
    default_ttl: int = int(timedelta(minutes=10).total_seconds())
    list_repos_ttl: int = int(timedelta(days=1).total_seconds())
    list_issues_ttl: int = int(timedelta(hours=1).total_seconds())


class AppearanceSettings(BaseModel):
    dark_mode: bool = True
    # Settings to configure which UI elements to display by default
    show_command_log: bool = True
    show_actions: bool = True
    show_issues: bool = True
    show_pull_requests: bool = True


class Config(BaseModel):
    # This field is aliased because I can't spell :)
    appearance: AppearanceSettings = AppearanceSettings()
    repositories: RepositorySettings = RepositorySettings()
    pull_requests: PullRequestSettings = PullRequestSettings()
    issues: IssueSettings = IssueSettings()
    cache: CacheSettings = CacheSettings()
    api: ApiConfig = ApiConfig()

    @classmethod
    def load_config(cls) -> Self:
        if _CONFIG_FILE_LOCATION.exists():
            return cls(**json.loads(_CONFIG_FILE_LOCATION.read_text()))
        else:
            return cls()

    def save(self) -> None:
        CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE_LOCATION.write_text(self.model_dump_json(indent=4))

    @classmethod
    @contextmanager
    def to_edit(cls) -> Generator[Self, None, None]:
        current_config = cls.load_config()
        yield current_config
        current_config.save()


if __name__ == "__main__":
    print(f"Config file location: {_CONFIG_FILE_LOCATION} (exists => {_CONFIG_FILE_LOCATION.exists()})")
    print(Config.load_config().model_dump_json(indent=4))
