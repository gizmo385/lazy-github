from logging import Handler, LogRecord
import logging
from typing import Optional

from textual.app import ComposeResult
from textual.widgets import Log

from lazy_github.ui.widgets.common import LazyGithubContainer
from lazy_github.lib.logging import lg, LazyGithubLogFormatter


class CommandLogLoggingHandler(Handler):
    def __init__(self, command_log: "LazyGithubCommandLog") -> None:
        super().__init__(logging.INFO)
        self.command_log = command_log
        self.setFormatter(LazyGithubLogFormatter(include_exceptions=False))

    def emit(self, record: LogRecord) -> None:
        self.command_log.write_line(self.format(record))


class LazyGithubCommandLog(Log):
    _instance: Optional[Log] = None

    def on_mount(self) -> None:
        LazyGithubCommandLog._instance = self
        lg.addHandler(CommandLogLoggingHandler(self))


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
