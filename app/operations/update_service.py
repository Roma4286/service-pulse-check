from dataclasses import dataclass

from app.celery.tasks import ServiceScheduler
from app.models import Service
from app.repositories.service_repository import ServiceRepository

from .errors import (
    ServiceNotFoundError,
    ServicePersistenceError,
    ServiceSchedulingError,
    TimeoutGreaterThanIntervalError
)

@dataclass(frozen=True, slots=True)
class UpdateServiceDTO:
    service_id: int
    name: str | None
    is_active: bool | None
    interval_in_seconds: int | None
    timeout_in_seconds: float | None


@dataclass(kw_only=True, slots=True)
class UpdateService:
    scheduler: ServiceScheduler
    service_repository: ServiceRepository

    def __call__(self, *, dto: UpdateServiceDTO) -> Service:
        service = self.service_repository.get_service_by_id(dto.service_id)

        if service is None:
            raise ServiceNotFoundError(message=f"Service with id={dto.service_id} not found in the database")
        
        previous_is_active = service.is_active
        previous_interval_in_seconds = service.interval_in_seconds
        previous_timeout_in_seconds = service.timeout_in_seconds

        new_interval_in_seconds = (
            dto.interval_in_seconds if dto.interval_in_seconds is not None else previous_interval_in_seconds
        )
        new_timeout_in_seconds = (
            dto.timeout_in_seconds if dto.timeout_in_seconds is not None else previous_timeout_in_seconds
        )

        if new_timeout_in_seconds > new_interval_in_seconds:
            raise TimeoutGreaterThanIntervalError()


        try:
            service = self.service_repository.update_service(
                service_id=dto.service_id,
                name=dto.name,
                is_active=dto.is_active,
                interval_in_seconds=dto.interval_in_seconds,
                timeout_in_seconds=dto.timeout_in_seconds,
                is_db_transaction=True,
            )
        except Exception as e:
            raise ServicePersistenceError(service_id=dto.service_id, name=dto.name) from e
        new_is_active = service.is_active
        schedule_changed = (
            previous_interval_in_seconds != service.interval_in_seconds
            or previous_timeout_in_seconds != service.timeout_in_seconds
        )
        try:
            if previous_is_active and not new_is_active:
                self.scheduler.delete_task(dto.service_id)
            elif not previous_is_active and new_is_active:
                self.scheduler.create_task(
                    service_id=service.id,
                    url=service.url,
                    service_type=service.type,
                    interval_in_seconds=service.interval_in_seconds,
                    timeout_in_seconds=service.timeout_in_seconds,
                )
            elif new_is_active and schedule_changed:
                self.scheduler.delete_task(dto.service_id)
                self.scheduler.create_task(
                    service_id=service.id,
                    url=service.url,
                    service_type=service.type,
                    interval_in_seconds=service.interval_in_seconds,
                    timeout_in_seconds=service.timeout_in_seconds,
            )     
        except Exception as e:
            self.service_repository.db_rollback()
            raise ServiceSchedulingError(service_id=service.id) from e
        else:
            self.service_repository.db_commit()

        return service
