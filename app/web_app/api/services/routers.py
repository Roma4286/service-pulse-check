from flask import Blueprint

from flask_pydantic import validate

from app.models import Service, ServiceStatus
from app.repositories.service_repository import ServiceRepository
from app.database import Session as database_session
from app.celery.tasks import ServiceScheduler
from app.celery.celery_app import celery_app

from .schemas import ServiceCreateSchema, ServiceListQuerySchema, ServiceUpdateSchema
from ..responses import api_response, not_found

services_bp = Blueprint('services', __name__, url_prefix='/services')

STATUS_TO_IS_ACTIVE = {
    "active": True,
    "inactive": False,
}

scheduler = ServiceScheduler(celery_app)

def serialize_service(service: Service) -> dict:
    return {
        "id": service.id,
        "name": service.name,
        "url": service.url,
        "type": service.type.value,
        "status": service.status.value,
        "interval_in_seconds": service.interval_in_seconds,
    }


@services_bp.route('', methods=['GET'])
@validate()
def get_services(query: ServiceListQuerySchema):
    is_active = STATUS_TO_IS_ACTIVE.get(query.status) if query.status else None

    service_repo = ServiceRepository(database_session())
    services = service_repo.get_services(is_active=is_active)
    return api_response(data={"services": [serialize_service(service) for service in services]})


@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service_repo = ServiceRepository(database_session())
    service = service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    return api_response(data=serialize_service(service))


@services_bp.route('', methods=['POST'])
@validate()
def create_service(body: ServiceCreateSchema):
    service_repo = ServiceRepository(database_session())
    service = service_repo.create_new_service(
        name=body.name, url=str(body.url), type=body.type, interval_in_seconds=body.interval_in_seconds
    )
    scheduler.create_task(
        service_id=service.id,
        url=str(body.url),
        service_type=body.type,
        interval_in_seconds=body.interval_in_seconds,
    )
    return api_response(data=serialize_service(service), status_code=201)


@services_bp.route('/<int:service_id>', methods=['PATCH'])
@validate()
def update_service(service_id, body: ServiceUpdateSchema):
    service_repo = ServiceRepository(database_session())
    service = service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    previous_status = service.status
    previous_interval_in_seconds = service.interval_in_seconds

    service = service_repo.update_service(
        service_id,
        name=body.name,
        status=body.status,
        interval_in_seconds=body.interval_in_seconds,
    )

    new_status = service.status

    if previous_status == ServiceStatus.ACTIVE and new_status == ServiceStatus.INACTIVE:
        scheduler.delete_task(service_id)
    elif previous_status == ServiceStatus.INACTIVE and new_status == ServiceStatus.ACTIVE:
        scheduler.create_task(
            service_id=service.id, url=service.url,
            service_type=service.type, interval_in_seconds=service.interval_in_seconds,
        )
    elif new_status == ServiceStatus.ACTIVE and previous_interval_in_seconds != service.interval_in_seconds:
        scheduler.delete_task(service_id)
        scheduler.create_task(
            service_id=service.id, url=service.url,
            service_type=service.type, interval_in_seconds=service.interval_in_seconds,
    )


    return api_response(data=serialize_service(service))


@services_bp.route('/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    service_repo = ServiceRepository(database_session())
    deleted = service_repo.delete_service(service_id)
    if not deleted:
        return not_found("Service not found")

    scheduler.delete_task(service_id)

    return api_response(status_code=204)
