from .base_service_error import BaseServiceError


class ServicePersistenceError(BaseServiceError):
    """Failed to save the service to the database."""


class ServiceSchedulingError(BaseServiceError):
    """Failed to schedule the service check."""

class ServiceNotFoundError(BaseServiceError):
    """Service not found in the database."""

class TimeoutGreaterThanIntervalError(BaseServiceError):
    """timeout_in_seconds must not be greater than interval_in_seconds."""