from flask import Blueprint, g, request

from flask_jwt_extended import create_access_token
from flask_pydantic_spec import Response

from app.models import User
from app.web_app.extensions import spec

from .schemas import TokenResponseSchema, UserSchema, UserResponseSchema
from ..responses import api_response, error_response, unauthorized

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.post("/register")
@spec.validate(body=UserSchema, resp=Response("HTTP_409", HTTP_201=UserResponseSchema), tags=["auth"])
def register():
    body: UserSchema = request.context.body

    try:
        user: User = g.user_repo.create_new_user(username=body.username, password=body.password)
    except Exception:
        g.user_repo.db_rollback()
        return error_response(409, "Username is already taken")

    return api_response(data={"username": user.username}, status_code=201)

@auth_bp.route('/login', methods=['POST'])
@spec.validate(body=UserSchema, resp=Response("HTTP_401", HTTP_200=TokenResponseSchema), tags=["auth"])
def login():
    body: UserSchema = request.context.body

    user: User = g.user_repo.get_user_by_username(username=body.username)
    if user is None or not user.check_password(password=body.password):
        return unauthorized("Invalid username or password")

    access_token = create_access_token(identity=str(user.id))
    return api_response(data={"access_token": access_token})
