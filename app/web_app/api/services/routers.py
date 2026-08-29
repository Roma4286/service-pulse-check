from flask import Blueprint, current_app, g, request

from flask_pydantic_spec import Response

from app.web_app import spec
from app.models import Service, CheckResult

from .schemas import (
    ServiceCreateSchema,
    ServiceListQuerySchema,
    ServiceUpdateSchema,
    ServiceResponseSchema,
    ServiceListResponseSchema,
    CheckResultListResponseSchema,
    ServiceSchema,
    CheckResultSchema,
)
from app.operations.create_service import CreateServiceDTO
from app.operations.update_service import UpdateServiceDTO
from app.operations.errors import ServiceNotFoundError, ServicePersistenceError, ServiceSchedulingError, TimeoutGreaterThanIntervalError

from ..responses import api_response, bad_request, error_response, not_found

services_bp = Blueprint('services', __name__, url_prefix='/services')


def serialize_service(service: Service) -> dict:
    return ServiceSchema.model_validate(service).model_dump(mode="json")


def serialize_check_result(check_result: CheckResult) -> dict:
    return CheckResultSchema.model_validate(check_result).model_dump(mode="json")


@services_bp.route('', methods=['GET'])
@spec.validate(query=ServiceListQuerySchema, resp=Response(HTTP_200=ServiceListResponseSchema), tags=["services"])
def get_services():
    query = request.context.query

    services = g.service_repo.get_services(is_active=query.is_active)
    return api_response(data={"services": [serialize_service(service) for service in services]})


@services_bp.route('/<int:service_id>', methods=['GET'])
@spec.validate(resp=Response("HTTP_404", HTTP_200=ServiceResponseSchema), tags=["services"])
def get_service(service_id):
    service = g.service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    return api_response(data=serialize_service(service))


@services_bp.route('', methods=['POST'])
@spec.validate(body=ServiceCreateSchema, resp=Response(HTTP_201=ServiceResponseSchema), tags=["services"])
def create_service():
    body: ServiceCreateSchema = request.context.body

    try:
        service = g.create_service(dto=CreateServiceDTO(
            name=body.name,
            url=str(body.url),
            type=body.type,
            interval_in_seconds=body.interval_in_seconds,
            timeout_in_seconds=body.timeout_in_seconds,
        ))
    except (ServicePersistenceError, ServiceSchedulingError) as e:
        return error_response(500, e.message)

    return api_response(data=serialize_service(service), status_code=201)


@services_bp.route('/<int:service_id>', methods=['PATCH'])
@spec.validate(body=ServiceUpdateSchema, resp=Response("HTTP_404", HTTP_200=ServiceResponseSchema), tags=["services"])
def update_service(service_id):
    body = request.context.body

    try:
        service = g.update_service(dto=UpdateServiceDTO(
            service_id=service_id,
            name=body.name,
            is_active=body.is_active,
            interval_in_seconds=body.interval_in_seconds,
            timeout_in_seconds=body.timeout_in_seconds,
        ))
    except (ServicePersistenceError, ServiceSchedulingError) as e:
        return error_response(500, e.message)
    except ServiceNotFoundError as e:
        return not_found(e.message)
    except TimeoutGreaterThanIntervalError as e:
        bad_request(e.message)
    
    return api_response(data=serialize_service(service))


@services_bp.route('/<int:service_id>', methods=['DELETE'])
@spec.validate(resp=Response("HTTP_204", "HTTP_404"), tags=["services"])
def delete_service(service_id):
    deleted = g.service_repo.delete_service(service_id)
    if not deleted:
        return not_found("Service not found")

    current_app.extensions["scheduler"].delete_task(service_id)

    return api_response(status_code=204)

@services_bp.route('/<int:service_id>/results', methods=['GET'])
@spec.validate(resp=Response("HTTP_404", HTTP_200=CheckResultListResponseSchema), tags=["services"])
def get_service_results(service_id):
    service = g.service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    results = g.check_result_repo.get_result_by_service_id(service_id)
    return api_response(data={"results": [serialize_check_result(result) for result in results]})


@services_bp.route('/<int:service_id>/results/<int:result_id>', methods=['DELETE'])
@spec.validate(resp=Response("HTTP_204", "HTTP_404"), tags=["services"])
def delete_service_result(service_id, result_id):
    deleted = g.check_result_repo.delete_result(result_id, service_id)
    if not deleted:
        return not_found("Result not found")

    return api_response(status_code=204)


@services_bp.route('/<int:service_id>/results', methods=['DELETE'])
@spec.validate(resp=Response("HTTP_204", "HTTP_404"), tags=["services"])
def delete_service_results(service_id):
    service = g.service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    g.check_result_repo.delete_results_by_service_id(service_id)
    return api_response(status_code=204)
