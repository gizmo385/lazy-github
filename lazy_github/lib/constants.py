from pathlib import Path

# Symbols used in various UI tables
IS_FAVORITED = "[green]★[/green]"
IS_NOT_FAVORITED = "☆"
IS_PRIVATE = "✔"
IS_PUBLIC = "✘"

CONFIG_FOLDER = Path.home() / ".config/lazy-github"


def favorite_string(favorite: bool) -> str:
    """Helper function to return the right string to indicate if something is favorited"""
    return IS_FAVORITED if favorite else IS_NOT_FAVORITED


def private_string(private: bool) -> str:
    """Helper function to return the right string to indicate if something is private"""
    return IS_PRIVATE if private else IS_PUBLIC
