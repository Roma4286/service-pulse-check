from flask import jsonify
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from werkzeug.http import HTTP_STATUS_CODES


def api_response(data=None, message=None, status_code=200):
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code


def api_response_set_auth_cookies(access_token: str, data=None, message=None, status_code=200):
    response, status_code = api_response(data=data, message=message, status_code=status_code)
    set_access_cookies(response, access_token)
    return response, status_code


def api_response_unset_auth_cookies(data=None, message=None, status_code=200):
    response, status_code = api_response(data=data, message=message, status_code=status_code)
    unset_jwt_cookies(response)
    return response, status_code


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
