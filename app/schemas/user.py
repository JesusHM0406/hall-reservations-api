from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.core.config import settings
from app.core.messages import ErrorMessages
from app.models.user_role import UserRole


class UserRead(BaseModel):
  id: int
  name: str

class UserCreate(BaseModel):
  name: str = Field(..., min_length=3, max_length=30)
  password: str = Field(..., min_length=settings.MIN_PASSWORD_SIZE, max_length=72)
  password_confirm: str = Field(..., min_length=settings.MIN_PASSWORD_SIZE, max_length=72)

  @model_validator(mode='after')
  def check_passwords_match(self) -> Self:
    pw1 = self.password
    pw2 = self.password_confirm

    if pw1 is not None and pw2 is not None and pw1 != pw2:
      raise ValueError(ErrorMessages.PASSWORDS_MISMATCH)
    return self

class UserUpdate(BaseModel):
  name: str = Field(..., min_length=3, max_length=30)

class UserAdminUpdate(BaseModel):
  name: str | None = Field(None, min_length=3, max_length=30)
  role: UserRole | None = Field(None)
  is_active: bool | None = Field(None)

class UserRestoreUpdate(BaseModel):
  name: str = Field(..., min_length=3, max_length=30)

class UserComplete(UserRead):
  role: str
  is_active: bool
  is_deleted: bool
