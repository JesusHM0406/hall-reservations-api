from pydantic import BaseModel, Field, field_validator

from app.core.messages import ErrorMessages

class HallCreate(BaseModel):
  name: str = Field(min_length=1, max_length=255)
  description: str = Field(min_length=1)
  is_available: bool

  @field_validator("name", "description")
  @classmethod
  def validate_not_empty(cls, v: str) -> str:
    if not v or not v.strip():
      raise ValueError(ErrorMessages.EMPTY_HALL_NAME)
    return v.strip()

class HallRead(BaseModel):
  id: int
  name: str
  description: str
  is_available: bool

class HallUpdate(BaseModel):
  name: str | None = Field(None, min_length=1, max_length=255)
  description: str | None = Field(None, min_length=1)
  is_available: bool | None

  @field_validator("name", "description")
  @classmethod
  def validate_not_empty(cls, v: str | None) -> str | None:
    if v is not None and (not v or not v.strip()):
      raise ValueError(ErrorMessages.EMPTY_HALL_NAME)
    return v.strip() if v is not None else None

class HallUpdateAvailability(BaseModel):
  is_available: bool

class HallSearchResponse(BaseModel):
  id: int
  name: str
  rank: float
