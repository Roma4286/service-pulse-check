class BaseServiceError(Exception):
    """Base service error."""
    def __init__(self, *, message: str = None, **context) -> None:
        self.message = message or self.__doc__
        self.context = context
