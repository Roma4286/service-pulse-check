from .base_service_error import BaseServiceError


class ServicePersistenceError(BaseServiceError):
    """Failed to save the service to the database."""


class ServiceSchedulingError(BaseServiceError):
    """Failed to schedule the service check."""
