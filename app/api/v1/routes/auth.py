from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DBDep
from app.core.config import settings
from app.core.messages import ErrorMessages
from app.core.security import authenticate_user, create_access_token
from app.utils.token import Token


router = APIRouter()

@router.post("/login")
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: DBDep
) -> Token:
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
