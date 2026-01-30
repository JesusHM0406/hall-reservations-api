from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import crud_create_new_user, crud_get_user_by_id, crud_get_user_by_name, crud_update_user, crud_delete_user
from app.models.user import User
from werkzeug.security import generate_password_hash

from app.schemas.user import UserRead

MIN_PASSWORD_SIZE = 8

async def service_create_user(db: AsyncSession, name: str, password: str, password_confirm: str) -> UserRead:
  if len(password) < MIN_PASSWORD_SIZE:
    raise ValueError("La contraseña debe contener al menos 8 caracteres.")
  if password != password_confirm:
    raise ValueError("Las contraseñas no coinciden.")

  async with db.begin():
    user = await crud_get_user_by_name(db, name)

    if user is not None:
      raise ValueError("El nombre de usuario ya existe")

    pw_hash = generate_password_hash(password)
    new_user: User = await crud_create_new_user(db, name, pw_hash)

  return UserRead(id=new_user.id, name=new_user.name)

async def service_get_user_by_id(db: AsyncSession, id: int) -> UserRead:
  user = await crud_get_user_by_id(db, id)

  if not user:
    raise ValueError("El usuario no existe")

  return UserRead(id=user.id, name=user.name )

async def service_update_user(db: AsyncSession, name: str, id: int) -> UserRead:
  async with db.begin():
    user = await crud_get_user_by_id(db, id)

    if not user:
      raise ValueError("El usuario no existe")

    await crud_update_user(db, name, id)

  return UserRead(id=id, name=name )

async def service_delete_user(db: AsyncSession, id: int):
  async with db.begin():
    user = await crud_get_user_by_id(db, id)

    if not user:
      raise ValueError("El usuario que intentas eliminar no existe")

    await crud_delete_user(db, id)

  return
