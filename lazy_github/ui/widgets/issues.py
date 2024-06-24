from typing import Dict

from textual.app import ComposeResult

from lazy_github.lib.messages import IssuesAndPullRequestsFetched
from lazy_github.models.github import Issue
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class IssuesContainer(LazyGithubContainer):
    issues: Dict[int, Issue] = {}
    status_column_index = -1
    number_column_index = -1
    title_column_index = -1

    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield LazyGithubDataTable(id="issues_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#issues_table", LazyGithubDataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("Status", key="status")
        self.table.add_column("Number", key="number")
        self.table.add_column("Author", key="author")
        self.table.add_column("Title", key="title")

        self.status_column_index = self.table.get_column_index("status")
        self.number_column_index = self.table.get_column_index("number")
        self.title_column_index = self.table.get_column_index("title")

    async def on_issues_and_pull_requests_fetched(self, message: IssuesAndPullRequestsFetched) -> None:
        message.stop()
        self.table.clear()
        self.issues = {}

        rows = []
        for issue in message.issues:
            self.issues[issue.number] = issue
            rows.append((issue.state, issue.number, issue.user.login, issue.title))
        self.table.add_rows(rows)
