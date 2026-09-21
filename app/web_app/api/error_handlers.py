from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from app.operations.base_service_error import BaseServiceError
from app.operations.errors import (
    ServiceNotFoundError,
    ServicePersistenceError,
    ServiceSchedulingError,
    TimeoutGreaterThanIntervalError,
)

from . import api_bp
from .responses import error_response, unauthorized

SERVICE_ERROR_STATUS_CODES: dict[type[BaseServiceError], int] = {
    ServiceNotFoundError: 404,
    TimeoutGreaterThanIntervalError: 400,
    ServicePersistenceError: 500,
    ServiceSchedulingError: 500,
}


@api_bp.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return error_response(e.code, e.description)


@api_bp.errorhandler(BaseServiceError)
def handle_service_error(e: BaseServiceError):
    status_code = SERVICE_ERROR_STATUS_CODES.get(type(e), 500)
    if status_code >= 500:
        current_app.logger.exception(e)
    return error_response(status_code, e.message)


@api_bp.errorhandler(JWTExtendedException)
@api_bp.errorhandler(PyJWTError)
def handle_jwt_error(e: Exception):
    return unauthorized(str(e))


@api_bp.errorhandler(Exception)
def handle_unexpected_exception(e: Exception):
    current_app.logger.exception(e)
    return error_response(500, "Internal server error")


def reformat_spec_validation_error(req, resp, req_validation_error, instance):
    """flask_pydantic_spec `before` hook: normalise validation errors to the API error format."""
    if req_validation_error is None:
        return

    errors = {
        ".".join(str(part) for part in error["loc"]): error["msg"]
        for error in resp.get_json()
    }
    payload, status_code = error_response(400, errors)
    resp.set_data(jsonify(payload).get_data())
    resp.status_code = status_code
    resp.headers["Content-Type"] = "application/json"
