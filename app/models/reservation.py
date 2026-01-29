from app.db.base_class import Base
from app.models.reservation_status import ReservationStatus
from sqlalchemy import Integer, Enum, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from app.models.user import User
  from app.models.hall import Hall

class Reservation(Base):
  __tablename__ = "reservations"
  __table_args__ = (UniqueConstraint("hall_id", "reservation_date", name="uq_hall_date"),)
  
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  hall_id: Mapped[int] = mapped_column(Integer, ForeignKey("halls.id"), nullable=False)
  status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus, name="reservation_status"), nullable=False, default=ReservationStatus.PENDING)
  reservation_date: Mapped[date] = mapped_column(Date, nullable=False)
  
  # Relationships
  user: Mapped["User"] = relationship("User", back_populates="reservations", lazy="raise")
  hall: Mapped["Hall"] = relationship("Hall", back_populates="reservations", lazy="raise")