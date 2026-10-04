from flask import Response, request

from . import web_bp

PUBLIC_ENDPOINTS = {"web.static", "web.auth.login", "web.auth.register"}


@web_bp.after_request
def forbid_storing_private_pages(response: Response) -> Response:
    if request.endpoint not in PUBLIC_ENDPOINTS:
        response.headers["Cache-Control"] = "no-store"
    return response
