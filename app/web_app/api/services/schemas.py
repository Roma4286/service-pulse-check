from typing import Literal

from pydantic import BaseModel, HttpUrl

from app.models import ServiceType, ServiceStatus


class ServiceListQuerySchema(BaseModel):
    status: Literal["active", "inactive"] | None = None


class ServiceCreateSchema(BaseModel):
    name: str
    url: HttpUrl
    type: ServiceType
    interval_in_seconds: int


class ServiceUpdateSchema(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my-service",
                "status": "active",
                "interval_in_seconds": 60,
            }
        }
    }

    name: str | None = None
    status: ServiceStatus | None = None
    interval_in_seconds: int | None = None


class ServiceSchema(BaseModel):
    id: int
    name: str
    url: str
    type: str
    status: str
    interval_in_seconds: int


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
