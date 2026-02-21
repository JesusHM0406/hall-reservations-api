from pydantic import BaseModel, Field

from app.core.config import settings


class UserRead(BaseModel):
  id: int
  name: str

class UserCreate(BaseModel):
  name: str = Field(..., min_length=3, max_length=30)
  password: str = Field(..., min_length=settings.MIN_PASSWORD_SIZE, max_length=72)
  password_confirm: str = Field(..., min_length=settings.MIN_PASSWORD_SIZE, max_length=72)

class UserUpdate(BaseModel):
  name: str

class UserComplete(UserRead):
  role: str
  is_active: bool
