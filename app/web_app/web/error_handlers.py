from flask import redirect, request, url_for
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from . import web_bp


def is_htmx_request() -> bool:
    return request.headers.get("HX-Request") == "true"


@web_bp.errorhandler(JWTExtendedException)
@web_bp.errorhandler(PyJWTError)
def redirect_to_login(e: Exception):
    login_url = url_for("web.auth.login")
    if is_htmx_request():
        return "", 401, {"HX-Redirect": login_url}
    return redirect(login_url)
