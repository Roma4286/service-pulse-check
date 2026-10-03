from flask import Blueprint, abort, g, render_template, request
from flask_jwt_extended import get_jwt_identity

from app.operations.update_service import UpdateService, UpdateServiceDTO
from app.repositories.service_repository import ServiceRepository
from app.web_app.extensions import protected

services_bp = Blueprint("services", __name__, url_prefix="/services")


@services_bp.post("/<int:service_id>/active")
@protected
def set_active(service_id):
    """htmx: switch a service on/off, return its card and the refreshed account stats."""
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
        "services/_service_card.html", service=service
    ) + render_template("_account_stats.html", services=services, oob=True)
