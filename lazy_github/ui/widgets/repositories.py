import asyncio
import json
from typing import Dict, Iterable

from textual import on, work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import DataTable

import lazy_github.lib.github.repositories as repos_api
from lazy_github.lib.bindings import LazyGithubBindings
from lazy_github.lib.cache import TABLE_CACHE_FOLDER
from lazy_github.lib.constants import IS_FAVORITED, favorite_string, private_string
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.backends.protocol import GithubApiRequestFailed
from lazy_github.lib.logging import lg
from lazy_github.lib.messages import RepoSelected
from lazy_github.models.github import Repository
from lazy_github.ui.screens.lookup_repository import LookupRepositoryModal
from lazy_github.ui.widgets.common import LazyGithubContainer, SearchableDataTable

_REPO_CACHE_PATH = TABLE_CACHE_FOLDER / "repos.json"


def _repo_to_row(repo: Repository) -> tuple[str, ...]:
    favorited = favorite_string(repo.full_name in LazyGithubContext.config.repositories.favorites)
    private = private_string(repo.private)
    return (favorited, repo.owner.login, repo.name, private)


class ReposContainer(LazyGithubContainer):
    BINDINGS = [
        LazyGithubBindings.TOGGLE_FAVORITE_REPO,
        LazyGithubBindings.LOOKUP_REPOSITORY,
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.repos: Dict[str, Repository] = {}
        self.favorite_column_index = -1
        self.owner_column_index = 1
        self.name_column_index = 1
        self.private_column_index = 1

    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield SearchableDataTable(
            id="searchable_repos_table",
            table_id="repos_table",
            search_input_id="repo_search",
            sort_key="favorite",
        )

    @property
    def searchable_table(self) -> SearchableDataTable:
        return self.query_one("#searchable_repos_table", SearchableDataTable)

    @property
    def table(self) -> DataTable:
        return self.searchable_table.table

    async def on_mount(self) -> None:
        # Setup the table
        self.table.cursor_type = "row"
        self.table.add_column(IS_FAVORITED, key="favorite")
        self.table.add_column("Owner", key="owner")
        self.table.add_column("Name", key="name")
        self.table.add_column("Private", key="private")

        self.favorite_column_index = self.table.get_column_index("favorite")
        self.owner_column_index = self.table.get_column_index("owner")
        self.name_column_index = self.table.get_column_index("name")
        self.private_column_index = self.table.get_column_index("private")

        self.load_repos()

    async def get_selected_repo(self) -> Repository:
        current_row = self.table.cursor_row
        owner = self.table.get_cell_at(Coordinate(current_row, self.owner_column_index))
        repo_name = self.table.get_cell_at(Coordinate(current_row, self.name_column_index))
        full_name = f"{owner}/{repo_name}"
        return self.repos[full_name]

    def add_repo_to_table(self, repo: Repository, write_cache: bool = True) -> None:
        self.repos[repo.full_name] = repo
        self.searchable_table.add_row(_repo_to_row(repo), key=repo.full_name)

        if write_cache:
            self.save_repo_cache()

    @work
    async def action_lookup_repository(self) -> None:
        if repository := await self.app.push_screen_wait(LookupRepositoryModal()):
            self.add_repo_to_table(repository)
            self.post_message(RepoSelected(repository))

    def save_repo_cache(self) -> None:
        lg.debug("Writing to repo cache")
        _REPO_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPO_CACHE_PATH.touch(exist_ok=True)
        _REPO_CACHE_PATH.write_text(json.dumps([r.model_dump(mode="json") for r in self.repos.values()]))

    async def load_repo_cache(self) -> None:
        lg.debug("reading from repo cache")
        if _REPO_CACHE_PATH.is_file():
            raw_output = json.loads(_REPO_CACHE_PATH.read_text())
            for raw_repo in raw_output:
                self.add_repo_to_table(Repository(**raw_repo), write_cache=False)

    def set_repositories(self, repos: Iterable[Repository]) -> None:
        self.repos = {}
        self.searchable_table.clear_rows()
        for repo in repos:
            self.add_repo_to_table(repo, write_cache=False)

        self.save_repo_cache()

    def check_current_directory_repo(self) -> None:
        """
        If the current user's directory is a git repo and they don't already have a git repo selected, try and mark that
        repo as the current repo.
        """
        if LazyGithubContext.current_directory_repo and not LazyGithubContext.current_repo:
            if repo := self.repos.get(LazyGithubContext.current_directory_repo):
                self.post_message(RepoSelected(repo))

    @work
    async def load_repos(self) -> None:
        # Loading the repos associated with the current account
        repos: list[Repository] = []
        await self.load_repo_cache()
        self.check_current_directory_repo()
        try:
            repos = await repos_api.list_all()
        except GithubApiRequestFailed:
            lg.exception("Error fetching repositories from Github API")

        # Loading any additionally tracked repos
        additional_repos_to_fetch = LazyGithubContext.config.repositories.additional_repos_to_track
        additional_repos = await asyncio.gather(
            *[repos_api.get_repository_by_name(full_repo_name) for full_repo_name in additional_repos_to_fetch]
        )
        repos.extend(filter(None, additional_repos))
        self.set_repositories(repos)
        self.check_current_directory_repo()

    async def action_toggle_favorite_repo(self):
        repo = await self.get_selected_repo()
        # Update the config to add/remove the favorite
        with LazyGithubContext.config.to_edit() as config:
            favorited = repo.full_name in config.repositories.favorites
            if favorited:
                lg.info(f"Unfavoriting repo {repo.full_name}")
                config.repositories.favorites.remove(repo.full_name)
            else:
                lg.info(f"Favoriting repo {repo.full_name}")
                config.repositories.favorites.append(repo.full_name)

        # Flip the state of the favorited column in the UI
        updated_favorited = repo.full_name in config.repositories.favorites
        self.table.update_cell(repo.full_name, "favorite", favorite_string(updated_favorited))
        self.searchable_table.sort_table()

    @on(DataTable.RowSelected, "#repos_table")
    async def repo_selected(self):
        # Bubble a message up indicating that a repo was selected
        repo = await self.get_selected_repo()
        self.post_message(RepoSelected(repo))
