from pydantic import BaseModel, HttpUrl

from app.models import ServiceType


class ServiceListQuerySchema(BaseModel):
    is_active: bool | None = None


class ServiceCreateSchema(BaseModel):
    name: str
    url: HttpUrl
    type: ServiceType
    interval_in_seconds: int
    timeout_in_seconds: float = 5.0


class ServiceUpdateSchema(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my-service",
                "is_active": True,
                "interval_in_seconds": 60,
                "timeout_in_seconds": 5.0,
            }
        }
    }

    name: str | None = None
    is_active: bool | None = None
    interval_in_seconds: int | None = None
    timeout_in_seconds: float | None = None


class ServiceSchema(BaseModel):
    id: int
    name: str
    url: str
    type: str
    is_active: bool
    interval_in_seconds: int
    timeout_in_seconds: float


class ServiceListDataSchema(BaseModel):
    services: list[ServiceSchema]


class CheckResultSchema(BaseModel):
    id: int
    service_id: int
    status: str
    response_time: float
    created_at: str


class CheckResultListDataSchema(BaseModel):
    results: list[CheckResultSchema]


class ServiceResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: ServiceSchema


class ServiceListResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: ServiceListDataSchema


class CheckResultListResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: CheckResultListDataSchema
