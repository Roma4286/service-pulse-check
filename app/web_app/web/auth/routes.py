from flask import Blueprint, g, redirect, render_template, request, url_for
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)

from app.models import User
from app.operations.errors import UsernameAlreadyTakenError
from app.operations.register_user import RegisterUser, RegisterUserDTO
from app.repositories.user_repository import UserRepository

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not password:
        return render_template(
            "register.html",
            error="Username and password are required",
            username=username,
        ), 400
    if password != confirm_password:
        return render_template(
            "register.html", error="Passwords do not match", username=username
        ), 400

    operation: RegisterUser = g.register_user
    try:
        operation(dto=RegisterUserDTO(username=username, password=password))
    except UsernameAlreadyTakenError as e:
        return render_template("register.html", error=e.message, username=username), 409

    return redirect(url_for("web.auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user_repo: UserRepository = g.user_repo

    user: User | None = user_repo.get_user_by_username(username=username)
    if user is None or not user.check_password(password=password):
        return render_template(
            "login.html", error="Invalid username or password", username=username
        ), 401

    response = redirect(url_for("web.home"))
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response


@auth_bp.post("/logout")
def logout():
    response = redirect(url_for("web.auth.login"))
    unset_jwt_cookies(response)
    return response
