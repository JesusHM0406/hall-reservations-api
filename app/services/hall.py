from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.hall import crud_create_new_hall, crud_get_hall_by_name
from app.schemas.hall import HallRead


async def service_create_new_hall(db: AsyncSession, name: str, description: str, is_available: bool) -> HallRead:
  async with db.begin():
    hall = await crud_get_hall_by_name(db, name)

    if hall:
      raise ValueError("There's already a hall with that name.")

    created_hall = await crud_create_new_hall(db, name, description, is_available)

  return HallRead(id=created_hall.id, name=name, description=description, is_available=is_available)
