from typing import Literal

from pydantic import BaseModel, HttpUrl

from app.models import ServiceType


class ServiceListQuerySchema(BaseModel):
    status: Literal["active", "inactive"] | None = None


class ServiceCreateSchema(BaseModel):
    name: str
    url: HttpUrl
    type: ServiceType


class ServiceUpdateSchema(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    type: ServiceType | None = None
