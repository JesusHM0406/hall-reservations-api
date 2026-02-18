from datetime import datetime, timezone, timedelta

from pwdlib import PasswordHash
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.user import crud_get_user_by_name
from app.schemas.user import UserComplete

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str):
  return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str):
  return password_hash.hash(password)

async def authenticate_user(db: AsyncSession, name: str, password: str):
  user = await crud_get_user_by_name(db, name)

  if not user:
    return False
  if not verify_password(password, user.pw_hash):
    return False

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active
  )

def create_access_token(data: dict, expires_delta: timedelta | None = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = (
      datetime.now(timezone.utc) +
      timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
    to_encode,
    settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
  )
  return encoded_jwt
