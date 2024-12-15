from lazy_github.lib.context import LazyGithubContext, github_headers
from lazy_github.lib.github.backends.protocol import GithubApiRequestFailed
from lazy_github.lib.logging import lg
from lazy_github.models.github import Repository, Workflow, WorkflowRun


async def list_workflows(repository: Repository, page: int = 1, per_page: int = 30) -> list[Workflow]:
    """Lists available Github action workflows on the specified repo"""
    query_params = {"page": page, "per_page": per_page}
    url = f"/repos/{repository.owner.login}/{repository.name}/actions/workflows"
    try:
        response = await LazyGithubContext.client.get(url, params=query_params)
        response.raise_for_status()
        raw_json = response.json()
    except GithubApiRequestFailed:
        lg.exception("Error retrieving actions from the Github API")
        return []
    else:
        if workflows := raw_json.get("workflows"):
            return [Workflow(**w) for w in workflows]
        else:
            return []


async def list_workflow_runs(repository: Repository, page: int = 1, per_page: int = 30) -> list[WorkflowRun]:
    """Lists github workflows runs on the specified repo"""
    query_params = {"page": page, "per_page": per_page}
    url = f"/repos/{repository.owner.login}/{repository.name}/actions/runs"

    try:
        response = await LazyGithubContext.client.get(url, params=query_params)
        response.raise_for_status()
        raw_json = response.json()
    except GithubApiRequestFailed:
        lg.exception("Error retrieving action runs from the Github API")
        return []
    else:
        if workflows := raw_json.get("workflow_runs"):
            return [WorkflowRun(**w) for w in workflows]
        else:
            return []


async def create_dispatch_event(repository: Repository, workflow: Workflow, branch: str) -> bool:
    """
    Creates a workflow dispatch event for the specified workflow. For properly configured workflows, this will trigger
    a new one against the specified branch
    """
    url = f"/repos/{repository.owner.login}/{repository.name}/actions/workflows/{workflow.id}/dispatches"
    body = {"ref": branch}
    response = await LazyGithubContext.client.post(url, headers=github_headers(), json=body)
    try:
        response.raise_for_status()
    except GithubApiRequestFailed:
        lg.exception("Error creating workflow dispatch event!")
    if not response.is_success:
        lg.error(f"Error creating workflow dispatch event: {response}")
    return response.is_success
