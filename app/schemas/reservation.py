from datetime import date, datetime, timezone, timedelta

from pydantic import BaseModel, field_validator

from app.core.messages import ErrorMessages


class ReservationCreate(BaseModel):
  hall_id: int
  reservation_date: date

  @field_validator('hall_id')
  @classmethod
  def validate_hall_id(cls, v: int) -> int:
    if v <= 0:
      raise ValueError("Hall ID must be a positive integer")
    return v

  @field_validator('reservation_date')
  @classmethod
  def validate_future_date(cls, v: date) -> date:
    today = datetime.now(timezone.utc).date()

    if v <= today:
      raise ValueError(ErrorMessages.INVALID_DATE)
    
    # Prevent reservations too far in the future
    max_future_date = today + timedelta(days=365)
    if v > max_future_date:
      raise ValueError("Reservations cannot be made more than 1 year in advance")

    return v

class ReservationRead(BaseModel):
  id: int
  user_id: int
  user_name: str
  hall_id: int
  hall_name: str
  status: str
  reservation_date: date
