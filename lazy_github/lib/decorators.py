class classproperty:
    """Simple implementation of the @property decorator but for classes"""

    def __init__(self, func):
        self.fget = func

    def __get__(self, _, owner):
        return self.fget(owner)
