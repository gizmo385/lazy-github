import click
import rich
import shutil

from lazy_github.lib.config import _CONFIG_FILE_LOCATION, Config
from lazy_github.lib.context import LazyGithubContext
from lazy_github.ui.app import app


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """A Terminal UI for interacting with Github"""
    if ctx.invoked_subcommand is None:
        run()


@cli.command
def run():
    """Run LazyGithub"""
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
    cache_directory = LazyGithubContext.config.cache.cache_directory
    if no_confirm or click.confirm(f"Confirm deletion of everything in {cache_directory}"):
        if cache_directory.exists():
            shutil.rmtree(cache_directory)
        print("Cache cleared")
    else:
        print("Canceling cache deletion")
