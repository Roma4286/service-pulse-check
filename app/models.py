import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ServiceStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class ServiceType(enum.Enum):
    HTTP = "http"
    TCP = "tcp"

class ResultStatus(enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    status: Mapped[ServiceStatus] = mapped_column(Enum(ServiceStatus))
    type: Mapped[ServiceType] = mapped_column(Enum(ServiceType))
    interval_in_seconds: Mapped[int] = mapped_column()

    checks: Mapped[list["CheckResult"]] = relationship("CheckResult", back_populates="service", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    service: Mapped["Service"] = relationship("Service", back_populates="checks")

    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus))

    response_time: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())