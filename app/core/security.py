from datetime import datetime, timezone, timedelta
from typing import cast

from pwdlib import PasswordHash
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.user import crud_get_user_by_name
from app.schemas.user import UserComplete

# Use recommended secure password hashing (Argon2id by default)
# This provides protection against brute-force and rainbow table attacks
password_hash = PasswordHash.recommended()

def verify_password(*, plain_password: str, hashed_password: str):
  return password_hash.verify(plain_password, hashed_password)

def get_password_hash(*, password: str):
  return password_hash.hash(password)

async def authenticate_user(*, db: AsyncSession, name: str, password: str):
  user = await crud_get_user_by_name(db=db, name=name)

  if not user:
    return False
  if not verify_password(plain_password=password, hashed_password=user.pw_hash):
    return False

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active,
    is_deleted=user.is_deleted
  )

def create_access_token(*, data: dict[str, object], expires_delta: timedelta | None = None) -> str:
  to_encode: dict[str, object] = data.copy()
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = (
      datetime.now(timezone.utc) +
      timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
  to_encode.update({"exp": expire})
  # PyJWT's key parameter has incomplete type stubs (Unknown | PyJWK | str | bytes)
  encoded_jwt = cast(
    str | bytes | bytearray | memoryview,
    jwt.encode(  # type: ignore[misc]
    to_encode,
    settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
    )
  )
  if isinstance(encoded_jwt, str):
    return encoded_jwt
  return bytes(encoded_jwt).decode("utf-8")
