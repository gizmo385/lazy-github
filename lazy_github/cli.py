import shutil
import socket
from contextlib import suppress

import click
import rich

from lazy_github.lib.config import _CONFIG_FILE_LOCATION, Config
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.backends.protocol import BackendType
from lazy_github.lib.github.client import OfflineModeEnabledError
from lazy_github.ui.app import app

_CLI_CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
_TEST_HOSTNAME = "one.one.one.one"


def _internet_available() -> bool:
    try:
        socket.gethostbyname(_TEST_HOSTNAME)
        return True
    except OSError:
        return False


@click.group(invoke_without_command=True, context_settings=_CLI_CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """A Terminal UI for interacting with Github"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command
@click.option("--offline", is_flag=True, default=False, help="Run in offline mode, disabling network requests")
@click.option(
    "--auth-backend",
    help="Specifies which authentication backend to use",
    envvar="AUTH_BACKEND",
    type=click.Choice(list(BackendType)),
)
def run(offline: bool, auth_backend: BackendType | None):
    """Run LazyGithub"""
    if auth_backend:
        with Config.to_edit() as config:
            config.api.client_type = auth_backend
    if offline or not _internet_available():
        LazyGithubContext.offline_mode = offline

    app.run()


@cli.command
def dump_config():
    """Dump the current configuration, as it would be loaded by LazyGithub"""
    print(f"Config file location: {_CONFIG_FILE_LOCATION} (exists => {_CONFIG_FILE_LOCATION.exists()})")
    rich.print_json(Config.load_config().model_dump_json())


@cli.command
def clear_auth():
    """Clears out any existing authentication config for LazyGithub, forcing the user to relogin"""
    from lazy_github.lib.github.auth import _AUTHENTICATION_CACHE_LOCATION

    _AUTHENTICATION_CACHE_LOCATION.unlink(missing_ok=True)


@cli.command
def clear_config():
    """Reset the user's settings"""
    _CONFIG_FILE_LOCATION.unlink(missing_ok=True)
    print("Your settings have been cleared")


@cli.command
@click.option("--no-confirm", is_flag=True, default=False, help="Don't ask for confirmation")
def clear_cache(no_confirm: bool):
    """Reset the lazy-github cache"""
    from lazy_github.lib.context import LazyGithubContext

    cache_directory = LazyGithubContext.config.cache.cache_directory
    if no_confirm or click.confirm(f"Confirm deletion of everything in {cache_directory}"):
        if cache_directory.exists():
            shutil.rmtree(cache_directory)
        print("Cache cleared")
    else:
        print("Canceling cache deletion")
