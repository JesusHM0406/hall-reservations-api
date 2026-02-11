from typing import Annotated, AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError

from app.core.config import settings
from app.crud.user import crud_get_user_by_name
from app.db.session import AsyncSession, AsyncSessionLocal
from app.schemas.user import UserComplete


async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    yield session

DBDep = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserComplete:
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    username = payload.get("sub")
    if username is None:
      raise credentials_exception
  except PyJWTError as e:
    print("deps.py get_current_user:")
    print(e)
    raise credentials_exception

  async with AsyncSessionLocal() as db:
    user = await crud_get_user_by_name(db, username)

  if user is None:
    raise credentials_exception

  return UserComplete(id=user.id, name=user.name, role=user.role, is_active=user.is_active)

async def get_current_active_user(user: Annotated[UserComplete, Depends(get_current_user)]):
  if not user.is_active:
    raise HTTPException(status_code=400, detail="Inactive user")
  return user

async def get_current_active_admin(user: Annotated[UserComplete, Depends(get_current_active_user)]):
  if user.role != "admin":
    raise HTTPException(status_code=403, detail="Not enough permissions.")
  return user
