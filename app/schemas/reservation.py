from pydantic import BaseModel
from datetime import date

class ReservationCreate(BaseModel):
  hall_id: int
  reservation_date: date

class ReservationRead(BaseModel):
  id: int
  user_id: int
  user_name: str
  hall_id: int
  hall_name: str
  status: str
  reservation_date: date
