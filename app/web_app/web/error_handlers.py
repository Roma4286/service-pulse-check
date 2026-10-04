from flask import current_app
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException

from app.operations.base_service_error import BaseServiceError
from app.operations.errors import ServiceNotFoundError

from . import web_bp
from .responses import (
    error_response,
    internal_error,
    not_found,
    service_unavailable,
    unauthorized,
)


@web_bp.errorhandler(JWTExtendedException)
@web_bp.errorhandler(PyJWTError)
def handle_jwt_error(e: Exception):
    return unauthorized()


@web_bp.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    if e.code == 404:
        return not_found()
    return error_response(e.description, e.code)


@web_bp.errorhandler(ServiceNotFoundError)
def handle_service_not_found(e: ServiceNotFoundError):
    return not_found()


@web_bp.errorhandler(BaseServiceError)
def handle_service_error(e: BaseServiceError):
    current_app.logger.exception("Service operation failed")
    return internal_error(e.message)


@web_bp.errorhandler(OperationalError)
def handle_database_unavailable(e: OperationalError):
    current_app.logger.exception("Database is unavailable")
    return service_unavailable()


@web_bp.errorhandler(Exception)
def handle_unexpected_exception(e: Exception):
    current_app.logger.exception("Unexpected error")
    return internal_error()
