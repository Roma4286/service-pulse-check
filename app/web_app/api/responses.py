from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException
from flask_pydantic.exceptions import ValidationError as PydanticValidationError
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


@api_bp.errorhandler(PydanticValidationError)
def handle_validation_error(e):
    errors = {
        field: value
        for field, value in {
            "body": e.body_params,
            "query": e.query_params,
            "path": e.path_params,
            "form": e.form_params,
        }.items()
        if value
    }
    return error_response(400, errors)


def reformat_spec_validation_error(req, resp, req_validation_error, instance):
    """`flask_pydantic_spec` raises validation failures as a raw WSGI
    response wrapped in a code-less HTTPException, which Flask returns
    unchanged and never routes through our errorhandlers. Rewrite the
    response body/status here, before it gets aborted, to match the
    shared error_response format."""
    if req_validation_error is None:
        return

    payload, status_code = error_response(400, resp.get_json())
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
