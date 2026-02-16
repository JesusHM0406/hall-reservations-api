from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DBDep
from app.core.config import settings
from app.core.security import authenticate_user, create_access_token
from app.utils.token import Token


router = APIRouter()

@router.post("/login")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DBDep) -> Token:
  async with db.begin():
    user = await authenticate_user(db, form_data.username, form_data.password)

  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(data={"sub": user.name}, expires_delta=access_token_expires)
  return Token(access_token=access_token, token_type="bearer")
