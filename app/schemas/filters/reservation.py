from enum import Enum
from pydantic import BaseModel, Field

from app.models.reservation_status import ReservationStatus


class ReservationFilters(BaseModel):
  user_id: int | None = Field(None, ge=1)
  hall_id: int | None = Field(None, ge=1)
  status: ReservationStatus | None = Field(None)

class ReservationFilterNames(str, Enum):
  USER = "user_id"
  HALL = "hall_id"
  STATUS = "status"

class ReservationFilterLabels(str, Enum):
  USER = "Filter by user id"
  HALL = "Filter by hall id"
  STATUS = "Reservation status"
