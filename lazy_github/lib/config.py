import json
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any, Generator, Literal, Optional

from pydantic import BaseModel, field_serializer, field_validator
from textual.theme import BUILTIN_THEMES, Theme

from lazy_github.lib.constants import CONFIG_FOLDER, IssueOwnerFilter, IssueStateFilter

_CONFIG_FILE_LOCATION = CONFIG_FOLDER / "config.json"

ISSUE_STATE_FILTER = Literal["all"] | Literal["open"] | Literal["closed"]
ISSUE_OWNER_FILTER = Literal["mine"] | Literal["all"]


class AppearanceSettings(BaseModel):
    """Settings focused on altering the appearance of LazyGithub, including hiding or showing different sections."""

    theme: Theme = BUILTIN_THEMES["textual-dark"]
    # Settings to configure which UI elements to display by default
    show_command_log: bool = True
    show_workflows: bool = True
    show_issues: bool = True
    show_pull_requests: bool = True

    @field_serializer("theme")
    @classmethod
    def serialize_theme(cls, theme: Theme | str) -> str:
        return theme.name if isinstance(theme, Theme) else theme

    @field_validator("theme", mode="before")
    @classmethod
    def validate_theme(cls, theme_name: Any) -> Theme:
        return BUILTIN_THEMES.get(theme_name, BUILTIN_THEMES["textual-dark"])


class NotificationSettings(BaseModel):
    """Controls the settings for the optional notification feature, which relies on the standard GitHub CLI."""

    enabled: bool = False
    show_all_notifications: bool = True


class BindingsSettings(BaseModel):
    """Custom keybinding overrides for LazyGithub. When rebinding, pressing ESCAPE will reset to the default binding."""

    overrides: dict[str, str] = {}


class RepositorySettings(BaseModel):
    """Repository-specific settings"""

    favorites: list[str] = []


class PullRequestSettings(BaseModel):
    """Changes how pull requests are retrieved from the Github API"""

    state_filter: IssueStateFilter = IssueStateFilter.ALL
    owner_filter: IssueOwnerFilter = IssueOwnerFilter.ALL


class IssueSettings(BaseModel):
    """Changes how issues are retrieved from the Github API"""

    state_filter: IssueStateFilter = IssueStateFilter.ALL
    owner_filter: IssueOwnerFilter = IssueOwnerFilter.ALL


class CacheSettings(BaseModel):
    """Settings that control how long data will be cached from the GitHub API"""

    cache_directory: Path = CONFIG_FOLDER / ".cache"
    default_ttl: int = int(timedelta(minutes=10).total_seconds())
    list_repos_ttl: int = int(timedelta(days=1).total_seconds())
    list_issues_ttl: int = int(timedelta(hours=1).total_seconds())


class CoreConfig(BaseModel):
    logfile_path: Path = CONFIG_FOLDER / "lazy_github.log"


class ApiConfig(BaseModel):
    """Controlling how the GitHub API is accessed in LazyGithub"""

    base_url: str = "https://api.github.com"


_CONFIG_INSTANCE: Optional["Config"] = None


class Config(BaseModel):
    appearance: AppearanceSettings = AppearanceSettings()
    notifications: NotificationSettings = NotificationSettings()
    bindings: BindingsSettings = BindingsSettings()
    repositories: RepositorySettings = RepositorySettings()
    pull_requests: PullRequestSettings = PullRequestSettings()
    issues: IssueSettings = IssueSettings()
    cache: CacheSettings = CacheSettings()
    core: CoreConfig = CoreConfig()
    api: ApiConfig = ApiConfig()

    @classmethod
    def load_config(cls) -> "Config":
        global _CONFIG_INSTANCE
        if _CONFIG_INSTANCE is None:
            if _CONFIG_FILE_LOCATION.exists():
                _CONFIG_INSTANCE = cls(**json.loads(_CONFIG_FILE_LOCATION.read_text()))
            else:
                _CONFIG_INSTANCE = cls()
        return _CONFIG_INSTANCE

    def save(self) -> None:
        CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE_LOCATION.write_text(self.model_dump_json(indent=4))

    @classmethod
    @contextmanager
    def to_edit(cls) -> Generator["Config", None, None]:
        current_config = cls.load_config()
        yield current_config
        current_config.save()


if __name__ == "__main__":
    print(f"Config file location: {_CONFIG_FILE_LOCATION} (exists => {_CONFIG_FILE_LOCATION.exists()})")
    print(Config.load_config().model_dump_json(indent=4))
