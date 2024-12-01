import json
import subprocess

from lazy_github.lib.logging import lg
from lazy_github.models.github import Notification

NOTIFICATIONS_PAGE_COUNT = 30


def _run_gh_cli_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Simple wrapper around running a Github CLI command"""
    full_command = ["gh"] + command
    return subprocess.run(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


async def is_logged_in() -> bool:
    """Checks to see if the user is currently logged into the GitHub CLI"""
    try:
        result = _run_gh_cli_command(["auth", "status"])
        return result.returncode == 0
    except Exception:
        lg.exception("Something is fucked")
        return False


async def fetch_notifications(all: bool) -> list[Notification]:
    """Fetches notifications on GitHub. If all=True, then previously read notifications will also be returned"""
    result = _run_gh_cli_command(["api", f"/notifications?all={str(all).lower()}"])
    notifications: list[Notification] = []
    lg.debug(result.stdout)
    lg.debug(result.stderr)
    if result.stdout:
        lg.debug(f"Stdout is {result.stdout}")
        parsed = json.loads(result.stdout.decode())
        notifications = [Notification(**n) for n in parsed]
    return notifications


async def mark_notification_as_read(notification: Notification) -> None:
    _run_gh_cli_command(["--method", "PATCH", "api", f"/notifications/threads/{notification.id}"])


async def unread_notification_count() -> int:
    """Returns the number of currently unread notifications on GitHub"""
    return len(await fetch_notifications(all=False))
