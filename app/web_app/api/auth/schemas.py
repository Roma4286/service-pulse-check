from typing import Annotated

from pydantic import BaseModel, StringConstraints

from ..services.schemas import CheckResultSchema, ServiceSchema


class UserSchema(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True)]
    password: str


class RegisterUserSchema(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=3,
            max_length=255,
        ),
    ]
    password: Annotated[str, StringConstraints(min_length=8)]


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
