import asyncio
import json
from dataclasses import dataclass

from lazy_github.lib.logging import lg
from lazy_github.models.github import Notification

NOTIFICATIONS_PAGE_COUNT = 30


@dataclass
class _FinishedCommand:
    returncode: int
    stdout: str
    stderr: str


async def _run_gh_cli_command(command: list[str]) -> _FinishedCommand:
    """Simple wrapper around running a Github CLI command"""
    proc = await asyncio.create_subprocess_exec(
        "gh", *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        raw_stdout, raw_stderr = await proc.communicate()
    except Exception:
        lg.exception("Couldn't communicate with gh cli proc")
        return _FinishedCommand(255, "", "")
    else:
        return_code = proc.returncode if proc.returncode is not None else 255
        return _FinishedCommand(return_code, raw_stdout.decode(), raw_stderr.decode())


async def is_logged_in() -> bool:
    """Checks to see if the user is currently logged into the GitHub CLI"""
    try:
        result = await _run_gh_cli_command(["auth", "status"])
        return result.returncode == 0
    except Exception:
        lg.exception("Error checking if github CLI is authenticated")
        return False


async def fetch_notifications(all: bool) -> list[Notification]:
    """Fetches notifications on GitHub. If all=True, then previously read notifications will also be returned"""
    result = await _run_gh_cli_command(["api", f"/notifications?all={str(all).lower()}"])
    notifications: list[Notification] = []
    if result.stdout:
        parsed = json.loads(result.stdout)
        notifications = [Notification(**n) for n in parsed]
    return notifications


async def mark_notification_as_read(notification: Notification) -> None:
    await _run_gh_cli_command(["--method", "PATCH", "api", f"/notifications/threads/{notification.id}"])


async def unread_notification_count() -> int:
    """Returns the number of currently unread notifications on GitHub"""
    return len(await fetch_notifications(all=False))
