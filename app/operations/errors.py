from .base_service_error import BaseServiceError


class ServicePersistenceError(BaseServiceError):
    """Failed to save the service to the database."""

class ServiceSchedulingError(BaseServiceError):
    """Failed to schedule the service check."""

class ServiceNotFoundError(BaseServiceError):
    """Service not found in the database."""

class TimeoutGreaterThanIntervalError(BaseServiceError):
    """timeout_in_seconds must not be greater than interval_in_seconds."""

class UserPersistenceError(BaseServiceError):
    """Failed to save the user to the database."""

class UsernameAlreadyTakenError(BaseServiceError):
    """Username is already taken"""