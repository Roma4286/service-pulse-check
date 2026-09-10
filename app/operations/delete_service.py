from dataclasses import dataclass

from app.celery.tasks import ServiceScheduler
from app.models import Service
from app.repositories.service_repository import ServiceRepository

from .errors import (
    ServiceNotFoundError,
    ServiceSchedulingError,
)

@dataclass(frozen=True, slots=True)
class DeleteServiceDTO:
    user_id: int
    service_id: int

@dataclass(kw_only=True, slots=True)
class DeleteService:
    scheduler: ServiceScheduler
    service_repository: ServiceRepository

    def __call__(self, *, dto: DeleteServiceDTO) -> Service:
        deleted = self.service_repository.delete_service(dto.user_id, dto.service_id, is_db_transaction=True)
        if not deleted:
            raise ServiceNotFoundError(message=f"Service with id={dto.service_id} not found in the database")

        try:
            self.scheduler.delete_task(dto.service_id)
        except Exception as e:
            self.service_repository.db_rollback()
            raise ServiceSchedulingError(service_id=dto.service_id) from e

        self.service_repository.db_commit()

        return True

