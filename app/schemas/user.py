from pydantic import BaseModel

class UserRead(BaseModel):
  id: str
  name: str

class UserCreate(BaseModel):
  name: str
  password: str

class UserUpdate(BaseModel):
  name: str
