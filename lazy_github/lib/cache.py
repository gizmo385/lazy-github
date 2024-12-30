import json
from typing import Iterable, TypeVar

from pydantic import BaseModel

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.logging import lg
from lazy_github.models.github import Repository

T = TypeVar("T", bound=BaseModel)


def load_models_from_cache(repo: Repository | None, cache_name: str, expect_type: type[T]) -> list[T]:
    """Loads information from a file cache where the cached information changes based on the repository"""
    results: list[T] = []
    if repo:
        filename = f"{repo.full_name.replace('/', '_')}_{cache_name}.json"
    else:
        filename = f"{cache_name}.json"
    cache_path = LazyGithubContext.config.cache.cache_directory / filename
    lg.debug(f"Loading cached data from: {cache_path}")

    if cache_path.is_file():
        cached_objects = json.loads(cache_path.read_text())
        for raw_obj in cached_objects:
            results.append(expect_type(**raw_obj))
    return results


def save_models_to_cache(repo: Repository | None, cache_name: str, objects: Iterable[T]) -> None:
    """Stores information in a file cache where the cached information changes based on the repository"""
    if repo:
        filename = f"{repo.full_name.replace('/', '_')}_{cache_name}.json"
    else:
        filename = f"{cache_name}.json"
    cache_path = LazyGithubContext.config.cache.cache_directory / filename
    lg.debug(f"Saving cached data to: {cache_path}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.touch(exist_ok=True)
    cache_path.write_text(json.dumps([o.model_dump(mode="json") for o in objects]))
