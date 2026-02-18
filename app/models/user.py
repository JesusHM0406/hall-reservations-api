from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import true

from app.db.base_class import Base
from app.models.user_role import UserRole

if TYPE_CHECKING:
  from app.models.reservation import Reservation

class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
  pw_hash: Mapped[str] = mapped_column(String(255), nullable=False)
  role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.USER, nullable=False)
  is_active: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=False)

  # Relationships
  reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="user", lazy="raise")
