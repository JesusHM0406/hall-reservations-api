from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.hall import (
  crud_create_new_hall,
  crud_delete_hall,
  crud_get_all_halls,
  crud_get_hall_by_id,
  crud_get_hall_by_name,
  crud_update_hall,
)
from app.schemas.hall import HallRead


async def service_create_new_hall(db: AsyncSession, name: str, description: str, is_available: bool) -> HallRead:
  async with db.begin():
    hall = await crud_get_hall_by_name(db, name)

    if hall:
      raise ValueError("There's already a hall with that name.")

    created_hall = await crud_create_new_hall(db, name, description, is_available)

  return HallRead(id=created_hall.id, name=name, description=description, is_available=is_available)

async def service_get_hall_by_id(db: AsyncSession, id: int) -> HallRead:
  async with db.begin():
    hall = await crud_get_hall_by_id(db, id)

    if not hall:
      raise ValueError("Hall not found.")

  return HallRead(id=hall.id, name=hall.name, description=hall.description, is_available=hall.is_available)

async def service_get_hall_by_name(db: AsyncSession, name: str) -> HallRead:
  async with db.begin():
    hall = await crud_get_hall_by_name(db, name)

    if not hall:
      raise ValueError("Hall not found.")

  return HallRead(id=hall.id, name=hall.name, description=hall.description, is_available=hall.is_available)

async def service_update_hall(db: AsyncSession, name: str | None, description: str | None, is_available: bool | None, id: int) -> HallRead:
  async with db.begin():
    hall = await crud_get_hall_by_id(db, id)

    if not hall:
      raise ValueError("Hall not found.")

    updated_hall = await crud_update_hall(hall, name, description, is_available)

  return HallRead(id=updated_hall.id, name=updated_hall.name, description=updated_hall.description, is_available=updated_hall.is_available)

async def service_delete_hall(db: AsyncSession, id: int):
  async with db.begin():
    hall = await crud_get_hall_by_id(db, id)

    if not hall:
      raise ValueError("The hall you want to delete doesn't exist.")

    await crud_delete_hall(db, id)

  return

async def service_get_all_halls(db: AsyncSession):
  async with db.begin():
    result = await crud_get_all_halls(db)

  data = [HallRead(id=row.id, name=row.name, description=row.description, is_available=row.is_available) for row in result]

  return data
