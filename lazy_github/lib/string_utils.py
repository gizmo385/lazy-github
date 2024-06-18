def pluralize(count: int, singular: str, plural: str):
    """
    Helper function for correctly pluralizing strings in the UI. This is simple but gets messy when written many times
    across the UI code.
    """
    return f"{count} {singular}" if count == 1 else f"{count} {plural}"
