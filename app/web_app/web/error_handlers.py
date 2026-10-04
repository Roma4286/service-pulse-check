from flask import current_app, redirect, render_template, request, url_for
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError
from werkzeug.exceptions import HTTPException

from app.operations.base_service_error import BaseServiceError
from app.operations.errors import ServiceNotFoundError

from . import web_bp

NOT_FOUND_MESSAGE = "Service not found. It may have been deleted."
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. Please try again."


def is_htmx_request() -> bool:
    return request.headers.get("HX-Request") == "true"


def error_response(message: str, status_code: int):
    if is_htmx_request():
        headers = {"HX-Retarget": "#toasts", "HX-Reswap": "beforeend"}
        return render_template("_toast.html", message=message), status_code, headers
    return (
        render_template("error.html", message=message, status_code=status_code),
        status_code,
    )


@web_bp.errorhandler(JWTExtendedException)
@web_bp.errorhandler(PyJWTError)
def redirect_to_login(e: Exception):
    login_url = url_for("web.auth.login")
    if is_htmx_request():
        return "", 401, {"HX-Redirect": login_url}
    return redirect(login_url)


@web_bp.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    message = NOT_FOUND_MESSAGE if e.code == 404 else e.description
    return error_response(message, e.code)


@web_bp.errorhandler(ServiceNotFoundError)
def handle_service_not_found(e: ServiceNotFoundError):
    return error_response(NOT_FOUND_MESSAGE, 404)


@web_bp.errorhandler(BaseServiceError)
def handle_service_error(e: BaseServiceError):
    current_app.logger.exception("Service operation failed")
    return error_response(e.message, 500)


@web_bp.errorhandler(Exception)
def handle_unexpected_exception(e: Exception):
    current_app.logger.exception("Unexpected error")
    return error_response(UNEXPECTED_ERROR_MESSAGE, 500)
