from pydantic import BaseModel


class HallCreate(BaseModel):
  name: str
  description: str
  is_available: bool

class HallRead(HallCreate):
  id: int

class HallUpdate(BaseModel):
  name: str | None
  description: str | None
  is_available: bool | None
