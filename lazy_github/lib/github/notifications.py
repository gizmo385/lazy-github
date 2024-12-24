import json
import re

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.backends.cli import run_gh_cli_command
from lazy_github.lib.github.pull_requests import get_full_pull_request
from lazy_github.lib.logging import lg
from lazy_github.models.github import FullPullRequest, Notification, NotificationSubject

NOTIFICATIONS_PAGE_COUNT = 30

_PULL_REQUEST_URL_REGEX = re.compile(r"[^:]+:[\/]+[^\/]+\/repos\/([^\/]+)\/([^\/]+)\/pulls\/(\d+)")


async def fetch_notifications(all: bool) -> list[Notification]:
    """Fetches notifications on GitHub. If all=True, then previously read notifications will also be returned"""
    notifications: list[Notification] = []
    try:
        result = await run_gh_cli_command(["api", f"/notifications?all={str(all).lower()}"])
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
