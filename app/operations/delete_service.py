from dataclasses import dataclass

from app.celery.tasks import ServiceScheduler
from app.models import Service
from app.repositories.service_repository import ServiceRepository

from .errors import (
    ServiceNotFoundError,
    ServiceSchedulingError,
)

@dataclass(kw_only=True, slots=True)
class DeleteService:
    scheduler: ServiceScheduler
    service_repository: ServiceRepository

    def __call__(self, *, service_id) -> Service:
        deleted = self.service_repository.delete_service(service_id, is_db_transaction=True)
        if not deleted:
            raise ServiceNotFoundError(message=f"Service with id={service_id} not found in the database")

        try:
            self.scheduler.delete_task(service_id)
        except Exception as e:
            self.service_repository.db_rollback()
            raise ServiceSchedulingError(service_id=service_id) from e

        self.service_repository.db_commit()

        return True

