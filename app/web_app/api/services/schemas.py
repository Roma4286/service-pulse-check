from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.models import ServiceType


class ServiceListQuerySchema(BaseModel):
    is_active: bool | None = None


class ServiceCreateSchema(BaseModel):
    name: str
    url: HttpUrl
    type: ServiceType
    interval_in_seconds: int = Field(gt=0)
    timeout_in_seconds: float = Field(default=5.0, gt=0)

    @model_validator(mode="after")
    def check_timeout_not_greater_than_interval(self):
        if self.timeout_in_seconds > self.interval_in_seconds:
            raise ValueError("timeout_in_seconds must not be greater than interval_in_seconds")
        return self


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
    interval_in_seconds: int | None = Field(default=None, gt=0)
    timeout_in_seconds: float | None = Field(default=None, gt=0)


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
