import json

from lazy_github.lib.github.backends.cli import run_gh_cli_command
from lazy_github.lib.logging import lg
from lazy_github.models.github import Notification

NOTIFICATIONS_PAGE_COUNT = 30


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
