from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES


def api_response(data=None, message=None, status_code=200):
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code


def error_response(status_code: int, message: str | dict | None = None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    return payload, status_code


def bad_request(message: str | None = None):
    return error_response(400, message)


def unauthorized(message: str | None = None):
    return error_response(401, message)


def not_found(message: str | None = None):
    return error_response(404, message)
