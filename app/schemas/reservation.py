from datetime import date, datetime, timezone

from pydantic import BaseModel, field_validator

from app.core.messages import ErrorMessages


class ReservationCreate(BaseModel):
  hall_id: int
  reservation_date: date

  @field_validator('reservation_date')
  @classmethod
  def validate_future_date(cls, v: date) -> date:
    today = datetime.now(timezone.utc).date()

    if v <= today:
      raise ValueError(ErrorMessages.INVALID_DATE)

    return v

class ReservationRead(BaseModel):
  id: int
  user_id: int
  user_name: str
  hall_id: int
  hall_name: str
  status: str
  reservation_date: date
