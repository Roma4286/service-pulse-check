from typing import Annotated

from pydantic import BaseModel, StringConstraints

from ..services.schemas import CheckResultSchema, ServiceSchema

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MIN_PASSWORD_LENGTH = 8


class UserSchema(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True)]
    password: str


class RegisterUserSchema(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=MIN_USERNAME_LENGTH,
            max_length=MAX_USERNAME_LENGTH,
        ),
    ]
    password: Annotated[str, StringConstraints(min_length=MIN_PASSWORD_LENGTH)]


class UsernameResponseSchema(BaseModel):
    username: str


class UserResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: UsernameResponseSchema


class UserInfoSchema(BaseModel):
    model_config = {"from_attributes": True}

    username: str


class AccountStatsSchema(BaseModel):
    services_total: int
    services_active: int


class ServiceWithLastResultSchema(ServiceSchema):
    last_result: CheckResultSchema | None


class MeDataSchema(BaseModel):
    user: UserInfoSchema
    stats: AccountStatsSchema
    services: list[ServiceWithLastResultSchema]


class MeResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: MeDataSchema
