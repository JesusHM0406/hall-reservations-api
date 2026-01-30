from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.crud.user import create_new_user, get_user_by_id
from app.models.user import User

MIN_PASSWORD_SIZE = 8

async def create_user(db: AsyncSession, name: str, password: str, password_confirm: str):
  if len(password) < MIN_PASSWORD_SIZE:
    raise ValueError("La contraseña debe contener al menos 8 caracteres.")
  if password != password_confirm:
    raise ValueError("Las contraseñas no coinciden.")

  async with db.begin():
    try:
      new_user: User = await create_new_user(db, name, password)
    except IntegrityError:
      raise ValueError("El nombre de usuario ya existe.")

  return {"id": new_user.id, "name": new_user.name }

async def get_user(db: AsyncSession, id: int):
  user = await get_user_by_id(db, id)

  if not user:
    raise ValueError("El usuario no existe")

  return { "id": user.id, "name": user.name }
