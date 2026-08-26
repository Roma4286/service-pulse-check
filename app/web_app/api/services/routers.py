from flask import Blueprint, abort

from flask_pydantic import validate

from app.models import Service
from app.repositories.service_repository import ServiceRepository
from app.database import Session as database_session

from .schemas import ServiceCreateSchema, ServiceListQuerySchema, ServiceUpdateSchema

services_bp = Blueprint('services', __name__, url_prefix='/services')

STATUS_TO_IS_ACTIVE = {
    "active": True,
    "inactive": False,
}


def serialize_service(service: Service) -> dict:
    return {
        "id": service.id,
        "name": service.name,
        "url": service.url,
        "type": service.type.value,
        "status": service.status.value,
    }


@services_bp.route('', methods=['GET'])
@validate()
def get_services(query: ServiceListQuerySchema):
    is_active = STATUS_TO_IS_ACTIVE.get(query.status) if query.status else None

    service_repo = ServiceRepository(database_session())
    services = service_repo.get_services(is_active=is_active)
    return {"services": [serialize_service(service) for service in services]}


@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service_repo = ServiceRepository(database_session())
    service = service_repo.get_service_by_id(service_id)
    if service is None:
        abort(404, description="Service not found")

    return serialize_service(service)


@services_bp.route('', methods=['POST'])
@validate()
def create_service(body: ServiceCreateSchema):
    service_repo = ServiceRepository(database_session())
    service = service_repo.create_new_service(
        name=body.name, url=str(body.url), type=body.type
    )
    return serialize_service(service), 201


@services_bp.route('/<int:service_id>', methods=['PATCH'])
@validate()
def update_service(service_id, body: ServiceUpdateSchema):
    service_repo = ServiceRepository(database_session())
    service = service_repo.update_service(
        service_id,
        name=body.name,
        url=str(body.url) if body.url is not None else None,
        type=body.type,
    )
    if service is None:
        abort(404, description="Service not found")

    return serialize_service(service)


@services_bp.route('/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    service_repo = ServiceRepository(database_session())
    deleted = service_repo.delete_service(service_id)
    if not deleted:
        abort(404, description="Service not found")

    return '', 204
