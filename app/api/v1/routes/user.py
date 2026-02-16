from fastapi import APIRouter

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.hall import Hall as Hall
from app.models.reservation import Reservation as Reservation
from app.models.user import User as User
from app.schemas.user import UserComplete, UserCreate, UserRead, UserUpdate
from app.services.user import (
  service_create_user,
  service_delete_user,
  service_get_all_users,
  service_get_user_by_id,
  service_update_user,
)
from app.utils.pagination_response import PaginationResponse

router = APIRouter()

@router.post("/", status_code=201)
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
  async with db.begin():
    return await service_create_user(db, user.name, user.password, user.password_confirm)

@router.get("/", response_model=PaginationResponse)
async def get_all_users(db: DBDep, admin: AdminDep, page: int = 1):
  return await service_get_all_users(db, page)

@router.get("/me")
async def read_current_user(user: UserDep) -> UserComplete:
  return user

@router.get("/{id}")
async def get_user_by_id(db: DBDep, admin: AdminDep, id: int) -> UserRead:
  async with db.begin():
    return await service_get_user_by_id(db, id)

@router.patch("/me")
async def update_current_user(db: DBDep, user: UserDep, update: UserUpdate) -> UserRead:
  async with db.begin():
    return await service_update_user(db, update.name, user.id)

@router.delete("/me", status_code=204)
async def delete_current_user(db: DBDep, user: UserDep):
  async with db.begin():
    await service_delete_user(db, user.id)
