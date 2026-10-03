from flask import Blueprint, abort, g, render_template, request
from flask_jwt_extended import get_jwt_identity

from app.models import CheckResult, Service
from app.operations.update_service import UpdateService, UpdateServiceDTO
from app.repositories.check_result_repository import CheckResultRepository
from app.repositories.service_repository import ServiceRepository
from app.web_app.extensions import protected

services_bp = Blueprint("services", __name__, url_prefix="/services")


def get_last_results(services: list[Service]) -> dict[int, CheckResult | None]:
    check_result_repo: CheckResultRepository = g.check_result_repo

    last_results = {}
    for service in services:
        results = check_result_repo.get_result_by_service_id(
            service.id, page=1, per_page=1
        )
        last_results[service.id] = results[0] if results else None
    return last_results


@services_bp.post("/<int:service_id>/active")
@protected
def set_active(service_id):
    user_id = int(get_jwt_identity())
    service_repo: ServiceRepository = g.service_repo
    operation: UpdateService = g.update_service

    if service_repo.get_service_by_id(user_id=user_id, service_id=service_id) is None:
        abort(404)

    service = operation(
        dto=UpdateServiceDTO(
            service_id=service_id,
            user_id=user_id,
            name=None,
            is_active=request.form.get("is_active") == "true",
            interval_in_seconds=None,
            timeout_in_seconds=None,
        )
    )

    services = service_repo.get_services(user_id=user_id)
    return render_template(
        "services/_service_card.html",
        service=service,
        last_results=get_last_results([service]),
    ) + render_template("_account_stats.html", services=services, oob=True)
