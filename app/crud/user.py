from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.user import User

async def crud_create_new_user(db: AsyncSession, name: str, pw_hash: str):
  new_user = User(name=name, pw_hash=pw_hash)
  db.add(new_user)
  return new_user

async def crud_get_user_by_id(db: AsyncSession, id: int):
  result = await db.execute(select(User.id, User.name).where(User.id == id))
  return result.first()

async def crud_update_user(db: AsyncSession, name: str, id: int):
  await db.execute(update(User).where(User.id == id).values(name=name))
  return

async def crud_delete_user(db: AsyncSession, id: int):
  await db.execute(delete(User).where(User.id == id))

async def crud_get_user_by_name(db: AsyncSession, name: str):
  result = await db.execute(select(User).where(User.name == name))
  return result.scalar_one_or_none()
