from functools import partial

from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, TabbedContent, TabPane

from lazy_github.lib.github.workflows import list_workflow_runs, list_workflows
from lazy_github.models.github import Repository, Workflow, WorkflowRun
from lazy_github.ui.widgets.common import LazilyLoadedDataTable, LazyGithubContainer


def workflow_to_cell(workflow: Workflow) -> tuple[str | int, ...]:
    return (workflow.name, workflow.created_at.strftime("%c"), workflow.updated_at.strftime("%c"), workflow.path)


def workflow_run_to_cell(run: WorkflowRun) -> tuple[str | int, ...]:
    return (run.created_at.strftime("%Y-%m-%d %H:%M"), run.conclusion or run.status, run.name, run.display_title)


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

    async def load_repo(self, repo: Repository) -> None:
        workflows = await list_workflows(repo)
        self.workflows = {}
        rows = []
        for workflow in workflows:
            self.workflows[workflow.name] = workflow
            rows.append(workflow_to_cell(workflow))

        self.searchable_table.set_rows(rows)
        self.searchable_table.change_load_function(partial(self.fetch_more_workflows, repo))
        self.searchable_table.can_load_more = True
        self.searchable_table.current_batch = 1


class WorkflowRunsContainer(Container):
    workflow_runs: dict[int, WorkflowRun] = {}

    def compose(self) -> ComposeResult:
        yield LazilyLoadedDataTable(
            id="searchable_workflow_runs_table",
            table_id="workflow_runs_table",
            search_input_id="workflow_runs_search",
            sort_key="time",
            load_function=None,
            batch_size=30,
            reverse_sort=True,
        )

    @property
    def searchable_table(self) -> LazilyLoadedDataTable:
        return self.query_one("#searchable_workflow_runs_table", LazilyLoadedDataTable)

    @property
    def table(self) -> DataTable:
        return self.query_one("#workflow_runs_table", DataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("Time", key="time")
        self.table.add_column("Result", key="result")
        self.table.add_column("Job Name", key="job_name")
        self.table.add_column("Run Name", key="run_name")

    async def fetch_more_workflow_runs(
        self, repo: Repository, batch_size: int, batch_to_fetch: int
    ) -> list[tuple[str | int, ...]]:
        next_page = await list_workflow_runs(repo, page=batch_to_fetch, per_page=batch_size)
        new_runs = [w for w in next_page if not isinstance(w, WorkflowRun)]
        self.workflow_runs.update({w.run_number: w for w in new_runs})

        return [workflow_to_cell(w) for w in new_runs]

    async def load_repo(self, repo: Repository) -> None:
        workflow_runs = await list_workflow_runs(repo)
        self.workflow_runs = {}
        rows = []
        for run in workflow_runs:
            self.workflow_runs[run.run_number] = run
            rows.append(workflow_run_to_cell(run))

        self.searchable_table.set_rows(rows)
        self.searchable_table.change_load_function(partial(self.fetch_more_workflow_runs, repo))
        self.searchable_table.can_load_more = True
        self.searchable_table.current_batch = 1


class WorkflowsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Workflows"
        with TabbedContent(id="workflow_tabs"):
            with TabPane("Workflows", id="workflows_tab"):
                yield AvailableWorkflowsContainers(id="workflows")
            with TabPane("Runs", id="runs_tab"):
                yield WorkflowRunsContainer(id="workflow_runs")

    @work
    async def load_repo(self, repo: Repository) -> None:
        await self.query_one("#workflows", AvailableWorkflowsContainers).load_repo(repo)
        await self.query_one("#workflow_runs", WorkflowRunsContainer).load_repo(repo)
