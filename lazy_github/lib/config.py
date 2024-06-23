import json
from contextlib import contextmanager
from typing import Generator, List, Literal, Self

from pydantic import BaseModel

from lazy_github.lib.constants import CONFIG_FOLDER

_CONFIG_FILE_LOCATION = CONFIG_FOLDER / "config.json"

PR_STATE_FILTER = Literal["all"] | Literal["open"] | Literal["closed"]


class ApiConfig(BaseModel):
    base_url: str = "https://api.github.com"


class PullRequestSettings(BaseModel):
    state_filter: PR_STATE_FILTER = "all"


class RepositorySettings(BaseModel):
    favorites: List[str] = []

    # TODO: We should add some caching here to make top level information retrieval more performant
    # We should have a configurable TTL for that information as well
    cache_duration: int = 1


class AppearenceSettings(BaseModel):
    dark_mode: bool = True


class Config(BaseModel):
    appearence: AppearenceSettings = AppearenceSettings()
    repositories: RepositorySettings = RepositorySettings()
    pull_requests: PullRequestSettings = PullRequestSettings()
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
    print(Config.load_config().model_dump_json(indent=4))
