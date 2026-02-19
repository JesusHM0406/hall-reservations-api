from pydantic import BaseModel, Field

from app.models.reservation_status import ReservationStatus


class ReservationFilters(BaseModel):
  user_id: int | None = Field(None, ge=1)
  hall_id: int | None = Field(None, ge=1)
  status: ReservationStatus | None = Field(None)
