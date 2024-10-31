from functools import partial

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Label, TabbedContent, TabPane

from lazy_github.lib.github.workflows import list_workflows
from lazy_github.lib.messages import RepoSelected
from lazy_github.models.github import Repository, Workflow
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazilyLoadedDataTable, LazyGithubContainer


def workflow_to_cell(workflow: Workflow) -> tuple[str | int, ...]:
    return (workflow.name, workflow.created_at.strftime("%c"), workflow.updated_at.strftime("%c"), workflow.path)


class AvailableWorkflowsContainers(Container):
    workflows: dict[str, Workflow] = {}

    def compose(self) -> ComposeResult:
        yield LazilyLoadedDataTable(
            id="searchable_workflows_table",
            table_id="workflows_table",
            search_input_id="workflows_search",
            sort_key="name",
            load_function=None,
            batch_size=30,
            reverse_sort=True,
        )

    @property
    def searchable_table(self) -> LazilyLoadedDataTable:
        return self.query_one("#searchable_workflows_table", LazilyLoadedDataTable)

    @property
    def table(self) -> DataTable:
        return self.query_one("#workflows_table", DataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("Name", key="name")
        self.table.add_column("Created", key="created")
        self.table.add_column("Updated", key="updated")
        self.table.add_column("Path", key="path")

    async def fetch_more_workflows(
        self, repo: Repository, batch_size: int, batch_to_fetch: int
    ) -> list[tuple[str | int, ...]]:
        next_page = await list_workflows(repo, page=batch_to_fetch, per_page=batch_size)
        new_workflows = [w for w in next_page if not isinstance(w, Workflow)]
        self.workflows.update({w.number: w for w in new_workflows})

        return [workflow_to_cell(w) for w in new_workflows]

    async def on_repo_selected(self, message: RepoSelected) -> None:
        log_event("Repo selected")
        workflows = await list_workflows(message.repo)
        self.workflows = {}
        rows = []
        for workflow in workflows:
            self.workflows[workflow.name] = workflow
            rows.append(workflow_to_cell(workflow))

        self.searchable_table.set_rows(rows)
        self.searchable_table.change_load_function(partial(self.fetch_more_workflows, message.repo))
        self.searchable_table.can_load_more = True
        self.searchable_table.current_batch = 1


class WorkflowRunsContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label("List of workflow runs")


class WorkflowsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Workflows"
        with TabbedContent(id="workflow_tabs"):
            with TabPane("Workflows", id="workflows_tab"):
                yield AvailableWorkflowsContainers(id="workflows")
            with TabPane("Runs", id="runs_tab"):
                yield WorkflowRunsContainer(id="workflow_runs")

    def on_repo_selected(self, message: RepoSelected) -> None:
        self.query_one("#workflows", AvailableWorkflowsContainers).post_message(message)
        self.query_one("#workflow_runs", WorkflowRunsContainer).post_message(message)
        # This prevents the message from endlessly cycling and DDOSing the app :)
        message.stop()
