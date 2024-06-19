from datetime import datetime
from typing import Optional

from textual import log
from textual.app import ComposeResult
from textual.widgets import Log

from lazy_github.ui.widgets.common import LazyGithubContainer


class LazyGithubCommandLog(Log):
    _instance: Optional[Log] = None

    def on_mount(self) -> None:
        LazyGithubCommandLog._instance = self


def log_event(message: str) -> None:
    "Helper function for writing to the textual log and displayed command log"
    log(message)
    log_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if LazyGithubCommandLog._instance:
        LazyGithubCommandLog._instance.write_line(f"{log_time}: {message}")


class CommandLogSection(LazyGithubContainer):
    DEFAULT_CSS = """
    CommandLogSection {
        height: 20%;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[6] Command Log"
        yield LazyGithubCommandLog()
