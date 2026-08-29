from dataclasses import dataclass

from app.celery.tasks import ServiceScheduler
from app.models import ServiceType, Service
from app.repositories.service_repository import ServiceRepository

from .errors import ServicePersistenceError, ServiceSchedulingError


@dataclass(frozen=True, slots=True)
class CreateServiceDTO:
    name: str
    url: str
    type: ServiceType
    interval_in_seconds: int
    timeout_in_seconds: float


@dataclass(kw_only=True, slots=True)
class CreateService:
    scheduler: ServiceScheduler
    service_repository: ServiceRepository

    def __call__(self, *, dto: CreateServiceDTO) -> Service:
        try:
            service = self.service_repository.create_new_service(
                name=dto.name,
                url=dto.url,
                type=dto.type,
                interval_in_seconds=dto.interval_in_seconds,
                timeout_in_seconds=dto.timeout_in_seconds,
                is_db_transaction=True,
            )
        except Exception as e:
            raise ServicePersistenceError(name=dto.name, url=dto.url) from e

        try:
            self.scheduler.create_task(
                service_id=service.id,
                url=dto.url,
                service_type=dto.type,
                interval_in_seconds=dto.interval_in_seconds,
                timeout_in_seconds=dto.timeout_in_seconds,
            )
        except Exception as e:
            self.service_repository.db_rollback()
            raise ServiceSchedulingError(service_id=service.id) from e
        else:
            self.service_repository.db_commit()

        return service
