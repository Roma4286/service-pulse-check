from flask import Blueprint, g, request
from flask_jwt_extended import create_access_token, get_jwt_identity
from flask_pydantic_spec import Response

from app.models import User
from app.operations.register_user import RegisterUser, RegisterUserDTO
from app.repositories.check_result_repository import CheckResultRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.web_app.extensions import protected, spec

from ..responses import (
    api_response,
    api_response_set_auth_cookies,
    api_response_unset_auth_cookies,
    unauthorized,
)
from ..services.schemas import ServiceSchema
from .schemas import (
    AccountStatsSchema,
    MeDataSchema,
    MeResponseSchema,
    ServiceWithLastResultSchema,
    UserInfoSchema,
    UserResponseSchema,
    UserSchema,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
@spec.validate(
    body=UserSchema,
    resp=Response("HTTP_409", HTTP_201=UserResponseSchema),
    tags=["auth"],
)
def register():
    body: UserSchema = request.context.body
    operation: RegisterUser = g.register_user

    user: User = operation(
        dto=RegisterUserDTO(username=body.username, password=body.password)
    )

    return api_response(data={"username": user.username}, status_code=201)


@auth_bp.route("/login", methods=["POST"])
@spec.validate(
    body=UserSchema,
    resp=Response("HTTP_401", HTTP_200=UserResponseSchema),
    tags=["auth"],
)
def login():
    body: UserSchema = request.context.body
    user_repo: UserRepository = g.user_repo

    user: User | None = user_repo.get_user_by_username(username=body.username)
    if user is None or not user.check_password(password=body.password):
        return unauthorized("Invalid username or password")

    access_token = create_access_token(identity=str(user.id))
    return api_response_set_auth_cookies(access_token, data={"username": user.username})


@auth_bp.post("/logout")
@spec.validate(resp=Response("HTTP_200"), tags=["auth"])
def logout():
    return api_response_unset_auth_cookies(message="Logged out")


@auth_bp.get("/me")
@protected
@spec.validate(
    resp=Response("HTTP_401", HTTP_200=MeResponseSchema),
    tags=["auth"],
)
def me():
    user_repo: UserRepository = g.user_repo
    service_repo: ServiceRepository = g.service_repo
    check_result_repo: CheckResultRepository = g.check_result_repo

    user: User | None = user_repo.get_user_by_id(int(get_jwt_identity()))
    if user is None:
        return unauthorized("User not found")

    services = service_repo.get_services(user_id=user.id)
    services_with_last_result = []
    for service in services:
        last_results = check_result_repo.get_result_by_service_id(
            service.id, page=1, per_page=1
        )
        services_with_last_result.append(
            ServiceWithLastResultSchema(
                **ServiceSchema.model_validate(service).model_dump(),
                last_result=last_results[0] if last_results else None,
            )
        )

    data = MeDataSchema(
        user=UserInfoSchema.model_validate(user),
        stats=AccountStatsSchema(
            services_total=len(services),
            services_active=sum(service.is_active for service in services),
        ),
        services=services_with_last_result,
    )
    return api_response(data=data.model_dump(mode="json"))
