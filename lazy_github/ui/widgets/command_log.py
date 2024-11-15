from datetime import datetime
from logging import Formatter, Handler, LogRecord
import logging
from typing import Optional

from textual import log as textual_log
from textual.app import ComposeResult
from textual.widgets import Log

from lazy_github.ui.widgets.common import LazyGithubContainer
from lazy_github.lib.logging import lg, lazy_github_log_formatter


class CommandLogLoggingHandler(Handler):
    def __init__(self, command_log: "LazyGithubCommandLog") -> None:
        super().__init__(logging.INFO)
        self.command_log = command_log
        self.setFormatter(lazy_github_log_formatter)

    def emit(self, record: LogRecord) -> None:
        self.command_log.write_line(self.format(record))


class LazyGithubCommandLog(Log):
    _instance: Optional[Log] = None

    def on_mount(self) -> None:
        LazyGithubCommandLog._instance = self
        lg.addHandler(CommandLogLoggingHandler(self))


def log_event(message: str, level=logging.INFO) -> None:
    "Helper function for writing to the textual log and displayed command log"
    textual_log(message)
    # log_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lg.log(level, message)
    # lg.log(level, f"{log_time}: {message}")


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
