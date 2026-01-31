from pydantic import BaseModel
from datetime import date

class ReservationCreate(BaseModel):
  user_id: int
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

class ReservationUpdate(BaseModel):
  status: str
