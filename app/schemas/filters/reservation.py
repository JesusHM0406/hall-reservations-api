from enum import Enum
from pydantic import BaseModel, Field

from app.models.reservation_status import ReservationStatus


class ReservationFilters(BaseModel):
  user_name: str | None = Field(None, min_length=3)
  hall_name: str | None = Field(None, min_length=3)
  status: ReservationStatus | None = Field(None)

class ReservationFilterNames(str, Enum):
  USER = "user_name"
  HALL = "hall_name"
  STATUS = "status"

class ReservationFilterLabels(str, Enum):
  USER = "Filter by user name"
  HALL = "Filter by hall name"
  STATUS = "Reservation status"
