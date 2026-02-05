from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from app.crud.user import (
  crud_create_new_user,
  crud_delete_user,
  crud_get_all_users,
  crud_get_user_by_id,
  crud_get_user_by_name,
  crud_update_user,
)
from app.exceptions.exceptions import BusinessLogicError, ConflictError, NotFoundError
from app.models.user import User
from app.schemas.user import UserRead

MIN_PASSWORD_SIZE = 8

async def service_create_user(db: AsyncSession, name: str, password: str, password_confirm: str) -> UserRead:
  if len(password) < MIN_PASSWORD_SIZE:
    raise BusinessLogicError("The password must contain at least 8 characters.")
  if password != password_confirm:
    raise BusinessLogicError("The passwords don't match.")

  user = await crud_get_user_by_name(db, name)

  if user is not None:
    raise ConflictError("The name already exists.")

  pw_hash = generate_password_hash(password)
  new_user: User = await crud_create_new_user(db, name, pw_hash)

  return UserRead(id=new_user.id, name=new_user.name)

async def service_get_user_by_id(db: AsyncSession, id: int) -> UserRead:
  user = await crud_get_user_by_id(db, id)

  if not user:
    raise NotFoundError("User not found.")

  return UserRead(id=user.id, name=user.name )

async def service_update_user(db: AsyncSession, name: str, id: int) -> UserRead:
  user = await crud_get_user_by_id(db, id)

  if not user:
    raise NotFoundError("User not found.")

  await crud_update_user(db, name, id)

  return UserRead(id=id, name=name )

async def service_delete_user(db: AsyncSession, id: int):
  user = await crud_get_user_by_id(db, id)

  if not user:
    raise NotFoundError("The user you want to delete doesn't exist.")

  await crud_delete_user(db, id)

  return

async def service_get_all_users(db: AsyncSession):
  result = await crud_get_all_users(db)

  data = []
  for row in result:
    data.append(UserRead(id=row.id, name=row.name))

  return data
