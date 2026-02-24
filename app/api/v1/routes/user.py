from typing_extensions import Annotated
from fastapi import APIRouter, Depends

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.reservation import Reservation as Reservation
from app.schemas.filters.user import UserFilters
from app.schemas.user import UserAdminUpdate, UserComplete, UserCreate, UserRead, UserRestoreUpdate, UserUpdate
from app.services.user import (
  service_create_user,
  service_delete_current_user,
  service_delete_user_as_admin,
  service_get_all_users,
  service_get_user_by_id,
  service_restore_user,
  service_update_user,
  service_update_user_as_admin,
)
from app.utils.pagination import Pagination

router = APIRouter()

@router.post("/", status_code=201, response_model=UserRead)
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
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

@router.patch("/me", response_model=UserRead)
async def update_current_user(
  db: DBDep,
  user: UserDep,
  update: UserUpdate
) -> UserRead:
  return await service_update_user(
    db=db,
    name=update.name,
    id=user.id
  )

@router.delete("/me", status_code=204)
async def delete_current_user(db: DBDep, user: UserDep):
  await service_delete_current_user(db=db, id=user.id)

@router.get("/{id}", response_model=UserComplete)
async def get_user_by_id(db: DBDep, admin: AdminDep, id: int) -> UserComplete:
  return await service_get_user_by_id(db=db, id=id)

@router.patch("/{id}", response_model=UserComplete)
async def update_user_as_admin(
  db: DBDep,
  admin: AdminDep,
  update: UserAdminUpdate,
  id: int
) -> UserComplete:
  return await service_update_user_as_admin(db=db, update=update, id=id)

@router.delete("/{id}", status_code=204)
async def delete_user_as_admin(db: DBDep, admin: AdminDep, id: int):
  await service_delete_user_as_admin(db=db, id_delete=id, admin=admin)

@router.patch("/{id}/restore", response_model=UserComplete)
async def restore_user(
  db: DBDep,
  admin: AdminDep,
  update: UserRestoreUpdate,
  id: int
):
  return await service_restore_user(db=db, id=id, new_name=update.name)
