import click

from lazy_github.lib.config import _CONFIG_FILE_LOCATION, Config
from lazy_github.ui.app import app


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
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
    print(Config.load_config().model_dump_json(indent=4))


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
