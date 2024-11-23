from enum import StrEnum
from pathlib import Path

# Content types
DIFF_CONTENT_ACCEPT_TYPE = "application/vnd.github.diff"
JSON_CONTENT_ACCEPT_TYPE = "application/vnd.github+json"

# App access information
LAZY_GITHUB_CLIENT_ID = "Iv23limdG8Bl3Cu5FOcT"
DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

# Symbols used in various UI tables
IS_FAVORITED = "[green]★[/green]"
IS_NOT_FAVORITED = "☆"
IS_PRIVATE = "✔"
IS_PUBLIC = "✘"

NOTIFICATION_REFRESH_INTERVAL = 60

CONFIG_FOLDER = Path.home() / ".config/lazy-github"


def favorite_string(favorite: bool) -> str:
    """Helper function to return the right string to indicate if something is favorited"""
    return IS_FAVORITED if favorite else IS_NOT_FAVORITED


def private_string(private: bool) -> str:
    """Helper function to return the right string to indicate if something is private"""
    return IS_PRIVATE if private else IS_PUBLIC


class IssueStateFilter(StrEnum):
    ALL = "all"
    OPEN = "open"
    CLOSED = "closed"


class IssueOwnerFilter(StrEnum):
    MINE = "mine"
    ALL = "all"
