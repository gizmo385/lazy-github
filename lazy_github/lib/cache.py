import json
from typing import Any, Callable, Iterable, TypeVar

from pydantic import BaseModel

from lazy_github.lib.constants import CONFIG_FOLDER
from lazy_github.models.github import Repository

TABLE_CACHE_FOLDER = CONFIG_FOLDER / "table-cache"
T = TypeVar("T", bound=BaseModel)


def load_repo_based_cache(repo: Repository, cache_name: str, expect_type: type[T]) -> list[T]:
    """Loads information from a file cache where the cached information changes based on the repository"""
    filename = TABLE_CACHE_FOLDER / f"{repo.full_name.replace('/', '_')}_{cache_name}.json"
    results: list[T] = []
    if filename.is_file():
        cached_objects = json.loads(filename.read_text())
        for raw_obj in cached_objects:
            results.append(expect_type(**raw_obj))
    return results


def save_repo_based_cache(repo: Repository, cache_name: str, objects: Iterable[T]) -> None:
    """Stores information in a file cache where the cached information changes based on the repository"""
    filename = TABLE_CACHE_FOLDER / f"{repo.full_name.replace('/', '_')}_{cache_name}.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.touch(exist_ok=True)
    filename.write_text(json.dumps([o.model_dump(mode="json") for o in objects]))
