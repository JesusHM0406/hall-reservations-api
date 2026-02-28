from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, func
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
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now()
)
  
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now()
)

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
    Index('idx_reservation_user_id', 'user_id'),
    Index('idx_reservation_status', 'status'),
    Index('idx_reservation_date', 'reservation_date'),
    Index('idx_reservation_user_status', 'user_id', 'status'),
  )
