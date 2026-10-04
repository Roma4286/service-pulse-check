from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    render_template,
    request,
    url_for,
)
from flask_jwt_extended import get_jwt_identity

from app.models import CheckResult, Service
from app.operations.base_service_error import BaseServiceError
from app.operations.create_service import CreateService, CreateServiceDTO
from app.operations.delete_service import DeleteService, DeleteServiceDTO
from app.operations.errors import ServiceNotFoundError
from app.operations.update_service import UpdateService, UpdateServiceDTO
from app.repositories.check_result_repository import (
    MAX_RESULTS_PER_PAGE,
    CheckResultRepository,
)
from app.repositories.service_repository import ServiceRepository
from app.web_app.extensions import protected

from .forms import parse_service_create_form
from .uptime import build_uptime

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


@services_bp.get("/<int:service_id>")
@protected
def detail(service_id):
    service_repo: ServiceRepository = g.service_repo

    service = service_repo.get_service_by_id(
        user_id=int(get_jwt_identity()), service_id=service_id
    )
    if service is None:
        abort(404)

    check_result_repo: CheckResultRepository = g.check_result_repo
    results = check_result_repo.get_result_by_service_id(
        service.id, page=1, per_page=MAX_RESULTS_PER_PAGE
    )
    return render_template(
        "service.html",
        service=service,
        last_results={service.id: results[0] if results else None},
        uptime=build_uptime(results, slots=MAX_RESULTS_PER_PAGE),
    )


@services_bp.post("/<int:service_id>/delete")
@protected
def delete(service_id):
    operation: DeleteService = g.delete_service

    try:
        operation(
            dto=DeleteServiceDTO(user_id=int(get_jwt_identity()), service_id=service_id)
        )
    except ServiceNotFoundError:
        abort(404)

    return "", 200, {"HX-Redirect": url_for("web.home")}


@services_bp.post("/<int:service_id>/active")
@protected
def set_active(service_id):
    user_id = int(get_jwt_identity())
    on_service_page = request.form.get("view") == "page"
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

    card = render_template(
        "services/_service_card.html",
        service=service,
        last_results=get_last_results([service]),
        on_service_page=on_service_page,
    )
    if on_service_page:
        return card

    services = service_repo.get_services(user_id=user_id)
    return card + render_template("_account_stats.html", services=services, oob=True)


@services_bp.get("/new")
@protected
def new_form():
    return render_template("services/_service_form.html", form={}, errors={})


@services_bp.get("/new-tile")
@protected
def new_tile():
    return render_template("services/_new_service_tile.html")


@services_bp.post("")
@protected
def create():
    user_id = int(get_jwt_identity())
    service_repo: ServiceRepository = g.service_repo
    operation: CreateService = g.create_service

    body, errors = parse_service_create_form(request.form)
    if body is None:
        return render_template(
            "services/_service_form.html", form=request.form, errors=errors
        )

    try:
        service = operation(
            dto=CreateServiceDTO(
                name=body.name,
                url=body.url,
                type=body.type,
                is_active=body.is_active,
                user_id=user_id,
                interval_in_seconds=body.interval_in_seconds,
                timeout_in_seconds=body.timeout_in_seconds,
            )
        )
    except BaseServiceError as e:
        current_app.logger.exception("Failed to create service")
        return render_template(
            "services/_service_form.html",
            form=request.form,
            errors={"__all__": e.message},
        )

    services = service_repo.get_services(user_id=user_id)
    return (
        render_template(
            "services/_service_card.html",
            service=service,
            last_results=get_last_results([service]),
        )
        + render_template("services/_new_service_tile.html")
        + render_template("_account_stats.html", services=services, oob=True)
    )
