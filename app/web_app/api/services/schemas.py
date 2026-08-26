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
    name: str | None = None
    status: ServiceStatus | None = None
    interval_in_seconds: int | None = None
