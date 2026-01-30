from fastapi import APIRouter, HTTPException

from app.api.deps import DBDep
from app.models.hall import Hall as Hall
from app.models.reservation import Reservation as Reservation
from app.models.user import User as User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import (
  service_create_user,
  service_delete_user,
  service_get_all_users,
  service_get_user_by_id,
  service_update_user,
)

router = APIRouter()

@router.post("/", status_code=201)
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
  try:
    user_created = await service_create_user(db, user.name, user.password, user.password_confirm)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"{e}")

  return user_created

@router.get("/all")
async def get_all_users(db: DBDep) -> list[UserRead]:
  result = await service_get_all_users(db)

  return result

@router.get("/{id}")
async def get_user_by_id(id: int, db: DBDep) -> UserRead:
  try:
    user = await service_get_user_by_id(db, id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return user

@router.patch("/{id}")
async def update_user(id: int, user: UserUpdate, db: DBDep) -> UserRead:
  try:
    updated_user = await service_update_user(db, user.name, id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return updated_user

@router.delete("/{id}", status_code=204)
async def delete_user(id: int, db: DBDep):
  try:
    await service_delete_user(db, id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return
