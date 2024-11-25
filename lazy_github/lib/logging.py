import logging

from lazy_github.lib.context import LazyGithubContext


# A universal logging format that we can use
class LazyGithubLogFormatter(logging.Formatter):
    def __init__(self, include_exceptions: bool = True) -> None:
        super().__init__("%(levelname)s %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        self.include_exceptions = include_exceptions

    def format(self, record: logging.LogRecord) -> str:
        if not self.include_exceptions:
            record.exc_info = None
            record.exc_text = None
        return super().format(record)


LazyGithubContext.config.core.logfile_path.parent.mkdir(parents=True, exist_ok=True)
lg = logging.Logger("lazy_github", level=logging.DEBUG)
_lg_file_handler = logging.FileHandler(filename=LazyGithubContext.config.core.logfile_path)
_lg_file_handler.setFormatter(LazyGithubLogFormatter())
lg.addHandler(_lg_file_handler)


# Override the logging level for a bunch of noisy library loggers
_LOGGERS_TO_MUTE = ["hishel", "httpx", "httpcore", "markdown_it", "asyncio"]
for other_logger_name in _LOGGERS_TO_MUTE:
    logging.getLogger(other_logger_name).setLevel(logging.WARNING)
