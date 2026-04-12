from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DBDep
from app.core.config import settings
from app.core.messages import ErrorMessages
from app.core.security import authenticate_user, create_access_token
from app.utils.rate_limit import login_rate_limiter
from app.utils.token import Token


router = APIRouter()

@router.post("/login")
async def login_for_access_token(
  request: Request,
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: DBDep
) -> Token:
  # Rate limiting by IP address
  client_ip = request.client.host if request.client else "unknown"
  
  is_allowed = await login_rate_limiter.is_allowed(client_ip)
  
  if not is_allowed:
    retry_after = await login_rate_limiter.get_retry_after(client_ip)
    headers: dict[str, str] = {}
    if retry_after:
      headers["Retry-After"] = str(retry_after)
    
    raise HTTPException(
      status_code=status.HTTP_429_TOO_MANY_REQUESTS,
      detail=f"Too many login attempts. Please try again after {retry_after} seconds.",
      headers=headers
    )
  
  user = await authenticate_user(
    db=db,
    name=form_data.username,
    password=form_data.password
  )

  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=ErrorMessages.UNAUTHORIZED,
      headers={"WWW-Authenticate": "Bearer"},
    )

  if user.is_deleted:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=ErrorMessages.DELETED_USER
    )

  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": str(user.id)},
    expires_delta=access_token_expires
  )
  return Token(access_token=access_token, token_type="bearer")
