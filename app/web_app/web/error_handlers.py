from flask import redirect, url_for
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from . import web_bp


@web_bp.errorhandler(JWTExtendedException)
@web_bp.errorhandler(PyJWTError)
def redirect_to_login(e: Exception):
    return redirect(url_for('web.auth.login'))
