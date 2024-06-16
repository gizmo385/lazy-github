from typing import List

from github.Repository import Repository
from textual import on, work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.message import Message

import lazy_github.lib.github as g
from lazy_github.lib.constants import IS_FAVORITED, IS_NOT_FAVORITED, IS_PRIVATE, IS_PUBLIC
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class RepoSelected(Message):
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        super().__init__()


class ReposContainer(LazyGithubContainer):
    BINDINGS = [
        ("f", "toggle_favorite_repo", "Toggle favorite"),
        ("enter", "select"),
    ]

    favorite_column_index: int = -1
    owner_column_index: int = 1
    name_column_index: int = 1
    private_column_index: int = 1

    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield LazyGithubDataTable(id="repos_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#repos_table", LazyGithubDataTable)

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

        # Let the UI load, then trigger this as a callback
        self.set_timer(0.1, self.load_repos)

    async def get_selected_repo(self) -> Repository:
        current_row = self.table.cursor_row
        owner = self.table.get_cell_at(Coordinate(current_row, self.owner_column_index))
        repo_name = self.table.get_cell_at(Coordinate(current_row, self.name_column_index))
        return g.github_client().get_repo(f"{owner}/{repo_name}")

    @work
    async def add_repos_to_table(self, repos: List[Repository]) -> None:
        rows = []
        for repo in repos:
            rows.append(
                [
                    IS_NOT_FAVORITED,
                    repo.owner.login,
                    repo.name,
                    IS_PRIVATE if repo.private else IS_PUBLIC,
                ]
            )
        self.table.add_rows(rows)

    @work(thread=True)
    def load_repos(self) -> None:
        user = g.github_client().get_user()
        repos = user.get_repos()
        self.add_repos_to_table(repos)

    async def action_toggle_favorite_repo(self):
        repo = await self.get_selected_repo()
        log_event(f"Favoriting repo {repo.full_name}")

    @on(LazyGithubDataTable.RowSelected, "#repos_table")
    async def repo_selected(self):
        # Bubble a message up indicating that a repo was selected
        repo = await self.get_selected_repo()
        self.post_message(RepoSelected(repo))
        log_event(f"Selected repo {repo.full_name}")
