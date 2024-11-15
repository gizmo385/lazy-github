import logging
from lazy_github.lib.context import LazyGithubContext

# A universal logging format that we can use
lazy_github_log_formatter = logging.Formatter(
    "%(levelname)s %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

lg = logging.Logger("lazy_github", level=logging.DEBUG)
_lg_file_handler = logging.FileHandler(filename=LazyGithubContext.config.core.logfile_path)
_lg_file_handler.setFormatter(lazy_github_log_formatter)
lg.addHandler(_lg_file_handler)


# Override the logging level for a bunch of noisy library loggers
_LOGGERS_TO_MUTE = ["hishel", "httpx", "httpcore", "markdown_it", "asyncio"]
for other_logger_name in _LOGGERS_TO_MUTE:
    logging.getLogger(other_logger_name).setLevel(logging.WARNING)
