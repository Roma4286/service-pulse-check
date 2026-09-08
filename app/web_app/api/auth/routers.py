from flask import Blueprint, g, request

from flask_jwt_extended import create_access_token
from flask_pydantic_spec import Response

from app.web_app.extensions import spec

from .schemas import TokenResponseSchema, UserLoginSchema
from ..responses import api_response, unauthorized

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
@spec.validate(body=UserLoginSchema, resp=Response("HTTP_401", HTTP_200=TokenResponseSchema), tags=["auth"])
def login():
    body: UserLoginSchema = request.context.body

    user = g.user_repo.get_user_by_username(body.username)
    if user is None or not user.check_password(body.password):
        return unauthorized("Invalid username or password")

    access_token = create_access_token(identity=str(user.id))
    return api_response(data={"access_token": access_token})
