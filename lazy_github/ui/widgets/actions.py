from textual.app import ComposeResult
from textual.widgets import DataTable

from lazy_github.lib.messages import RepoSelected
from lazy_github.ui.widgets.common import LazyGithubContainer


class ActionsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield DataTable(id="actions_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the actions for the selected repo
        message.stop()
