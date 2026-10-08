from pydantic import BaseModel

from ..services.schemas import CheckResultSchema, ServiceSchema


class UserSchema(BaseModel):
    username: str
    password: str


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
