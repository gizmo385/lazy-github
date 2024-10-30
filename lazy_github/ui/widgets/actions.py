from textual.app import ComposeResult
from textual.widgets import DataTable

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.actions import list_workflows
from lazy_github.lib.messages import RepoSelected
from lazy_github.models.github import Workflow
from lazy_github.ui.widgets.common import LazilyLoadedDataTable, LazyGithubContainer


def workflow_to_cell(workflow: Workflow) -> tuple[str | int, ...]:
    return (workflow.name, workflow.created_at.strftime("%c"), workflow.updated_at.strftime("%c"), workflow.path)


class ActionsContainer(LazyGithubContainer):
    workflows: dict[str, Workflow] = {}

    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield LazilyLoadedDataTable(
            id="searchable_actions_table",
            table_id="actions_table",
            search_input_id="workflows_search",
            sort_key="name",
            load_function=None,
            batch_size=30,
            reverse_sort=True,
        )

    @property
    def searchable_table(self) -> LazilyLoadedDataTable:
        return self.query_one("#searchable_actions_table", LazilyLoadedDataTable)

    @property
    def table(self) -> DataTable:
        return self.query_one("#actions_table", DataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("Name", key="name")
        self.table.add_column("Created", key="created")
        self.table.add_column("Updated", key="updated")
        self.table.add_column("Path", key="path")

    async def fetch_more_workflows(self, batch_size: int, batch_to_fetch: int) -> list[tuple[str | int, ...]]:
        if not LazyGithubContext.current_repo:
            return []

        next_page = await list_workflows(
            LazyGithubContext.current_repo,
            page=batch_to_fetch,
            per_page=batch_size,
        )

        new_workflows = [w for w in next_page if not isinstance(w, Workflow)]
        self.workflows.update({w.number: w for w in new_workflows})

        return [workflow_to_cell(w) for w in new_workflows]

    async def on_repo_selected(self, message: RepoSelected) -> None:
        message.stop()

        workflows = await list_workflows(message.repo)
        self.workflows = {}
        rows = []
        for workflow in workflows:
            self.workflows[workflow.name] = workflow
            rows.append(workflow_to_cell(workflow))

        self.searchable_table.set_rows(rows)
        self.searchable_table.change_load_function(self.fetch_more_workflows)
        self.searchable_table.can_load_more = True
        self.searchable_table.current_batch = 1
