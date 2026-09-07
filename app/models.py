import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.security import hash_password, verify_password

class Base(DeclarativeBase):
    pass

class ServiceType(enum.Enum):
    HTTP = "http"
    TCP = "tcp"

class ResultStatus(enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"

class User(Base):
    __tablename__ = "users"

    def __init__(self, name: str, password: str):
        self.name = name
        self.password_hash = hash_password(password)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    password_hash : Mapped[str] = mapped_column()

    services: Mapped[list["Service"]] = relationship("Service", back_populates="user", cascade="all, delete-orphan")

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    timeout_in_seconds: Mapped[float] = mapped_column(default=5.0)
    type: Mapped[ServiceType] = mapped_column(Enum(ServiceType))
    interval_in_seconds: Mapped[int] = mapped_column()

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship("User", back_populates="services")

    checks: Mapped[list["CheckResult"]] = relationship("CheckResult", back_populates="service", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    service: Mapped["Service"] = relationship("Service", back_populates="checks")

    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus))

    response_time: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())