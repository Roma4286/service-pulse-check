from flask import g, redirect, render_template, url_for
from flask_jwt_extended import get_jwt_identity

from app.repositories.user_repository import UserRepository
from app.web_app.extensions import protected

from . import web_bp


@web_bp.route("/")
@protected
def home():
    user_repo: UserRepository = g.user_repo

    user = user_repo.get_user_by_id(int(get_jwt_identity()))
    if user is None:
        return redirect(url_for("web.auth.login"))

    return render_template("home.html", user=user)
