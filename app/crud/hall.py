from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall


async def crud_get_hall_by_id(db: AsyncSession, id: int):
  result = await db.execute(select(Hall).where(Hall.id == id))
  return result.scalar_one_or_none()
