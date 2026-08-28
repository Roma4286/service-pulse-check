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
)
from ..responses import api_response, bad_request, not_found

services_bp = Blueprint('services', __name__, url_prefix='/services')


def serialize_service(service: Service) -> dict:
    return {
        "id": service.id,
        "name": service.name,
        "url": service.url,
        "type": service.type.value,
        "is_active": service.is_active,
        "interval_in_seconds": service.interval_in_seconds,
        "timeout_in_seconds": service.timeout_in_seconds,
    }


def serialize_check_result(check_result: CheckResult) -> dict:
    return {
        "id": check_result.id,
        "service_id": check_result.service_id,
        "status": check_result.status.value,
        "response_time": check_result.response_time,
        "created_at": check_result.created_at.isoformat(),
    }


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
    body = request.context.body

    service = g.service_repo.create_new_service(
        name=body.name,
        url=str(body.url),
        type=body.type,
        interval_in_seconds=body.interval_in_seconds,
        timeout_in_seconds=body.timeout_in_seconds,
    )
    current_app.extensions["scheduler"].create_task(
        service_id=service.id,
        url=str(body.url),
        service_type=body.type,
        interval_in_seconds=body.interval_in_seconds,
        timeout_in_seconds=body.timeout_in_seconds,
    )
    return api_response(data=serialize_service(service), status_code=201)


@services_bp.route('/<int:service_id>', methods=['PATCH'])
@spec.validate(body=ServiceUpdateSchema, resp=Response("HTTP_404", HTTP_200=ServiceResponseSchema), tags=["services"])
def update_service(service_id):
    body = request.context.body

    service = g.service_repo.get_service_by_id(service_id)
    if service is None:
        return not_found("Service not found")

    previous_is_active = service.is_active
    previous_interval_in_seconds = service.interval_in_seconds
    previous_timeout_in_seconds = service.timeout_in_seconds

    new_interval_in_seconds = (
        body.interval_in_seconds if body.interval_in_seconds is not None else previous_interval_in_seconds
    )
    new_timeout_in_seconds = (
        body.timeout_in_seconds if body.timeout_in_seconds is not None else previous_timeout_in_seconds
    )
    if new_timeout_in_seconds > new_interval_in_seconds:
        return bad_request("timeout_in_seconds must not be greater than interval_in_seconds")

    service = g.service_repo.update_service(
        service_id,
        name=body.name,
        is_active=body.is_active,
        interval_in_seconds=body.interval_in_seconds,
        timeout_in_seconds=body.timeout_in_seconds,
    )

    new_is_active = service.is_active
    schedule_changed = (
        previous_interval_in_seconds != service.interval_in_seconds
        or previous_timeout_in_seconds != service.timeout_in_seconds
    )
    scheduler = current_app.extensions["scheduler"]

    if previous_is_active and not new_is_active:
        scheduler.delete_task(service_id)
    elif not previous_is_active and new_is_active:
        scheduler.create_task(
            service_id=service.id,
            url=service.url,
            service_type=service.type,
            interval_in_seconds=service.interval_in_seconds,
            timeout_in_seconds=service.timeout_in_seconds,
        )
    elif new_is_active and schedule_changed:
        scheduler.delete_task(service_id)
        scheduler.create_task(
            service_id=service.id,
            url=service.url,
            service_type=service.type,
            interval_in_seconds=service.interval_in_seconds,
            timeout_in_seconds=service.timeout_in_seconds,
    )


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
