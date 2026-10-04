from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.celery.checkers.tcp import parse_address
from app.models import ResultStatus, ServiceType
from app.repositories.check_result_repository import MAX_RESULTS_PER_PAGE

MAX_TCP_PORT = 65535


class ServiceListQuerySchema(BaseModel):
    is_active: bool | None = None


class CheckResultListQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=MAX_RESULTS_PER_PAGE, ge=1)


def validate_http_url(url: str) -> str:
    try:
        return str(TypeAdapter(HttpUrl).validate_python(url))
    except ValidationError as e:
        raise ValueError(e.errors()[0]["msg"]) from e


def validate_tcp_address(address: str) -> str:
    try:
        host, port = parse_address(address)
    except ValueError:
        host, port = None, None

    if not host or port is None or not 1 <= port <= MAX_TCP_PORT:
        raise ValueError("TCP address must be host:port, e.g. db.example.com:5432")
    return address


class ServiceCreateSchema(BaseModel):
    name: str
    type: ServiceType
    url: str = Field(
        description="http(s) URL for http services, host:port for tcp services"
    )
    is_active: bool
    interval_in_seconds: int = Field(default=10.0, gt=0)
    timeout_in_seconds: float = Field(default=5.0, gt=0)

    @field_validator("url")
    @classmethod
    def check_url_matches_type(cls, url: str, info: ValidationInfo) -> str:
        url = url.strip()
        service_type = info.data.get("type")
        if service_type == ServiceType.HTTP:
            return validate_http_url(url)
        if service_type == ServiceType.TCP:
            return validate_tcp_address(url)
        return url

    @model_validator(mode="after")
    def check_timeout_not_greater_than_interval(self):
        if self.timeout_in_seconds > self.interval_in_seconds:
            raise ValueError(
                "timeout_in_seconds must not be greater than interval_in_seconds"
            )
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
    model_config = {"from_attributes": True}

    id: int
    name: str
    url: str
    type: ServiceType
    is_active: bool
    interval_in_seconds: int
    timeout_in_seconds: float


class ServiceListDataSchema(BaseModel):
    services: list[ServiceSchema]


class CheckResultSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    service_id: int
    status: ResultStatus
    response_time: float
    created_at: datetime


class CheckResultListDataSchema(BaseModel):
    results: list[CheckResultSchema]
    page: int
    per_page: int


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
