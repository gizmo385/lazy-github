def pluralize(count: int, singular: str, plural: str):
    """
    Helper function for correctly pluralizing strings in the UI. This is simple but gets messy when written many times
    across the UI code.
    """
    return f"{count} {singular}" if count == 1 else f"{count} {plural}"


def bold(s: str) -> str:
    """Wraps the given text in Rich bold tags"""
    return f"[bold]{s}[/bold]"


def link(link_text: str, url: str) -> str:
    """Formats a link in Rich-style markup"""
    return f"[link={url}]{link_text}[/link]"


class classproperty:
    """Simple implementation of the @property decorator but for classes"""

    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)
