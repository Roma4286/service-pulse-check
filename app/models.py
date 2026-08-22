import enum
from datetime import datetime

from sqlalchemy import Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ServiceStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    status: Mapped[ServiceStatus] = mapped_column(Enum(ServiceStatus))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column()
    status_code: Mapped[int] = mapped_column()
    response_time: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())