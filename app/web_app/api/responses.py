from flask import current_app, jsonify
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException

from app.operations.errors import (
    ServiceNotFoundError,
    ServicePersistenceError,
    ServiceSchedulingError,
    TimeoutGreaterThanIntervalError,
)

from . import api_bp


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    return payload, status_code


def bad_request(message):
    return error_response(400, message)


def not_found(message):
    return error_response(404, message)


@api_bp.errorhandler(HTTPException)
def handle_exception(e):
    return error_response(e.code)


@api_bp.errorhandler(ServiceNotFoundError)
def handle_service_not_found_error(e):
    return not_found(e.message)


@api_bp.errorhandler(TimeoutGreaterThanIntervalError)
def handle_timeout_greater_than_interval_error(e):
    return bad_request(e.message)


@api_bp.errorhandler(ServicePersistenceError)
@api_bp.errorhandler(ServiceSchedulingError)
def handle_service_error(e):
    return error_response(500, e.message)


@api_bp.errorhandler(Exception)
def handle_unexpected_exception(e):
    current_app.logger.exception(e)
    return error_response(500, "Internal server error")


def reformat_spec_validation_error(req, resp, req_validation_error, instance):
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


def api_response(data=None, message=None, status_code=200):
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code
