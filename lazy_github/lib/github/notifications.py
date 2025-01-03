import json
import re

from lazy_github.lib.context import LazyGithubContext, github_headers
from lazy_github.lib.github.backends.cli import build_command, run_gh_cli_command
from lazy_github.lib.github.pull_requests import get_full_pull_request
from lazy_github.lib.logging import lg
from lazy_github.models.github import FullPullRequest, Notification, NotificationSubject

NOTIFICATIONS_PAGE_COUNT = 50

_PULL_REQUEST_URL_REGEX = re.compile(r"[^:]+:[\/]+[^\/]+\/repos\/([^\/]+)\/([^\/]+)\/pulls\/(\d+)")


async def fetch_notifications(all: bool, per_page: int = NOTIFICATIONS_PAGE_COUNT, page: int = 1) -> list[Notification]:
    """Fetches notifications on GitHub. If all=True, then previously read notifications will also be returned"""
    notifications: list[Notification] = []
    query_params = {"all": str(all).lower(), "page": page, "per_page": per_page}
    try:
        notification_command = build_command("/notifications", query_params=query_params)
        result = await run_gh_cli_command(notification_command)
        if result.stdout:
            parsed = json.loads(result.stdout)
            notifications = [Notification(**n) for n in parsed]
    except Exception:
        lg.exception("Failed to retrieve notifications from the Github API")
    return notifications


async def mark_notification_as_read(notification: Notification) -> None:
    try:
        await run_gh_cli_command(["--method", "PATCH", "api", f"/notifications/threads/{notification.id}"])
    except Exception:
        lg.exception("Failed to mark notification as read")


async def unread_notification_count() -> int:
    """Returns the number of currently unread notifications on GitHub"""
    return len(await fetch_notifications(all=False))


async def extract_notification_subject(subject: NotificationSubject) -> FullPullRequest | None:
    """Attempts to connect the specified notification subject to another Github object, such as a PR"""
    if not (LazyGithubContext.current_repo and subject.url):
        return

    try:
        # Try and load a PR number from the subject URL
        if matches := _PULL_REQUEST_URL_REGEX.match(subject.url):
            pr_number = int(matches.group(3))
            return await get_full_pull_request(LazyGithubContext.current_repo, pr_number)
    except Exception:
        return None


async def mark_all_notifications_as_read() -> None:
    """Marks all of the current user's notifications as read"""
    result = await LazyGithubContext.client.put("/notifications", headers=github_headers(), json={"read": "true"})
    result.raise_for_status()
