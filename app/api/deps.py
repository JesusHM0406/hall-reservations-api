from typing import Annotated, AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from starlette.status import HTTP_400_BAD_REQUEST

from app.core.config import settings
from app.core.messages import ErrorMessages
from app.crud.user import crud_get_user_by_id
from app.db.session import AsyncSession, AsyncSessionLocal
from app.models.user_role import UserRole
from app.schemas.user import UserComplete


async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    async with session.begin():
      yield session

DBDep = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
  token: Annotated[str, Depends(oauth2_scheme)],
  db: DBDep
) -> UserComplete:
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=ErrorMessages.INVALID_CREDENTIALS,
      headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(
      token,
      settings.SECRET_KEY,
      algorithms=[settings.ALGORITHM]
    )
    id = payload.get("sub")
    if id is None:
      raise credentials_exception
  except PyJWTError:
    raise credentials_exception

  user = await crud_get_user_by_id(db=db, id=int(id))

  if user is None:
    raise credentials_exception

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active,
    is_deleted=user.is_deleted
  )

async def get_current_active_user(user: Annotated[UserComplete, Depends(get_current_user)]):
  if user.is_deleted:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=ErrorMessages.DELETED_USER
  )

  if not user.is_active:
    raise HTTPException(
      status_code=HTTP_400_BAD_REQUEST,
      detail=ErrorMessages.INACTIVE_USER
    )
  return user

async def get_current_active_admin(user: Annotated[UserComplete, Depends(get_current_active_user)]):
  if user.role != UserRole.ADMIN:
    raise HTTPException(
      status_code=403,
      detail=ErrorMessages.NOT_ENOUGH_PERMISSIONS
    )
  return user

UserDep = Annotated[UserComplete, Depends(get_current_active_user)]
AdminDep = Annotated[UserComplete, Depends(get_current_active_admin)]
