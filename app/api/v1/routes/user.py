from typing_extensions import Annotated
from fastapi import APIRouter, Depends

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.hall import Hall as Hall
from app.models.reservation import Reservation as Reservation
from app.models.user import User as User
from app.schemas.filters.user import UserFilters
from app.schemas.user import UserComplete, UserCreate, UserRead, UserUpdate
from app.services.user import (
  service_create_user,
  service_delete_user,
  service_get_all_users,
  service_get_user_by_id,
  service_update_user,
)
from app.utils.pagination import Pagination

router = APIRouter()

@router.post("/", status_code=201, response_model=UserRead)
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
  async with db.begin():
    return await service_create_user(
      db=db,
      name=user.name,
      password=user.password,
      password_confirm=user.password_confirm
    )

@router.get("/", response_model=Pagination)
async def get_all_users(
  db: DBDep,
  admin: AdminDep,
  filters: Annotated[UserFilters, Depends()],
  page: int = 1
) -> Pagination:
  return await service_get_all_users(
    db=db,
    page=page,
    filters=filters
  )

@router.get("/me", response_model=UserComplete)
async def read_current_user(user: UserDep) -> UserComplete:
  return user

@router.get("/{id}", response_model=UserComplete)
async def get_user_by_id(db: DBDep, admin: AdminDep, id: int) -> UserComplete:
  return await service_get_user_by_id(db=db, id=id)

@router.patch("/me", response_model=UserRead)
async def update_current_user(
  db: DBDep,
  user: UserDep,
  update: UserUpdate
) -> UserRead:
  async with db.begin():
    return await service_update_user(
      db=db,
      name=update.name,
      id=user.id
    )

@router.delete("/me", status_code=204)
async def delete_current_user(db: DBDep, user: UserDep):
  async with db.begin():
    await service_delete_user(db=db, id=user.id)
