from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall


async def crud_get_hall_by_id(db: AsyncSession, id: int):
  result = await db.execute(select(Hall).where(Hall.id == id))
  return result.scalar_one_or_none()

async def crud_get_hall_by_name(db: AsyncSession, name: str):
  result = await db.execute(select(Hall).where(Hall.id == name))
  return result.scalar_one_or_none()

async def crud_update_hall(hall: Hall, name: str | None, description: str | None, is_available: bool | None):
  if name:
    hall.name = name
  if description:
    hall.description = description
  if is_available is not None:
    hall.is_available = is_available

  return hall

async def crud_delete_hall(db: AsyncSession, id: int):
  await db.execute(delete(Hall).where(Hall.id == id))

async def crud_get_all_halls(db: AsyncSession):
  result = await db.execute(select(Hall))

  return result
