from textual.app import ComposeResult

from lazy_github.lib.messages import RepoSelected
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class IssuesContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield LazyGithubDataTable(id="issues_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the issues for the selected repo
        message.stop()
