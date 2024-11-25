import asyncio
import json
from asyncio.subprocess import PIPE, Process

NOTIFICATIONS_PAGE_COUNT = 30


async def _run_gh_cli_command(command: str) -> Process:
    """Simple wrapper around running a Github CLI command"""
    return await asyncio.create_subprocess_shell(f"gh {command}", stdout=PIPE, stderr=PIPE)


async def is_logged_in() -> bool:
    """Checks to see if the user is currently logged into the GitHub CLI"""
    try:
        result = await _run_gh_cli_command("auth status")
        await result.wait()
        return result.returncode == 0
    except Exception:
        return False


async def fetch_notifications(all: bool) -> list[str]:
    """Fetches notifications on GitHub. If all=True, then previously read notifications will also be returned"""
    result = await _run_gh_cli_command(f'api "/notifications?all={str(all).lower()}"')
    await result.wait()
    notifications: list[str] = []
    if result.stdout:
        stdout = await result.stdout.read()
        parsed = json.loads(stdout.decode())
        notifications = [n["subject"]["title"] for n in parsed]
    return notifications


async def unread_notification_count() -> int:
    """Returns the number of currently unread notifications on GitHub"""
    return len(await fetch_notifications(all=False))
