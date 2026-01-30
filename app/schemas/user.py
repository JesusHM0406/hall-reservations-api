from pydantic import BaseModel

class UserRead(BaseModel):
  id: int
  name: str

class UserCreate(BaseModel):
  name: str
  password: str
  password_confirm: str

class UserUpdate(BaseModel):
  name: str
