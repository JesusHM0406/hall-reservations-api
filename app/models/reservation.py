from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.reservation_status import ReservationStatus

if TYPE_CHECKING:
  from app.models.hall import Hall
  from app.models.user import User

class Reservation(Base):
  __tablename__ = "reservations"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  hall_id: Mapped[int] = mapped_column(Integer, ForeignKey("halls.id"), nullable=False)
  status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus, name="reservation_status"), nullable=False, default=ReservationStatus.CONFIRMED)
  reservation_date: Mapped[date] = mapped_column(Date, nullable=False)

  # Relationships
  user: Mapped["User"] = relationship("User", back_populates="reservations", lazy="raise")
  hall: Mapped["Hall"] = relationship("Hall", back_populates="reservations", lazy="raise")

  __table_args__ = (
    Index(
      'uq_hallid_resdate_active',
      'hall_id', 'reservation_date',
      unique=True,
      postgresql_where=(
        status == ReservationStatus.CONFIRMED
      )
    ),
  )
