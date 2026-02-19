from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.crud.user import (
  crud_create_new_user,
  crud_delete_user,
  crud_get_all_users,
  crud_get_user_by_id,
  crud_get_user_by_name,
  crud_update_user,
)
from app.exceptions.exceptions import BusinessLogicError, ConflictError, NotFoundError
from app.schemas.filters.user import UserFilters
from app.schemas.user import UserComplete, UserRead
from app.utils.filters_metadata import UserFilterLabels, UserFilterNames
from app.utils.pagination import Pagination, get_pagination
from app.utils.pagination_filters import FilterFactory

MIN_PASSWORD_SIZE = 8

async def service_create_user(
  *,
  db: AsyncSession,
  name: str,
  password: str,
  password_confirm: str
) -> UserRead:
  if len(password) < MIN_PASSWORD_SIZE:
    raise BusinessLogicError("The password must contain at least 8 characters.")
  if password != password_confirm:
    raise BusinessLogicError("The passwords don't match.")

  user = await crud_get_user_by_name(db=db, name=name)

  if user is not None:
    raise ConflictError("The name already exists.")

  pw_hash = get_password_hash(password=password)
  new_user = await crud_create_new_user(db=db, name=name, pw_hash=pw_hash)

  await db.flush()

  return UserRead(id=new_user.id, name=new_user.name)

async def service_get_user_by_id(
  *,
  db: AsyncSession,
  id: int
) -> UserComplete:
  user = await crud_get_user_by_id(db=db, id=id)

  if not user:
    raise NotFoundError("User not found.")

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active
  )

async def service_update_user(
  *,
  db: AsyncSession,
  name: str,
  id: int
) -> UserRead:
  user = await crud_get_user_by_id(db=db, id=id)

  if not user:
    raise NotFoundError("User not found.")
  if not user.is_active:
    raise BusinessLogicError("The user is inactive.")

  await crud_update_user(db=db, name=name, id=id)

  return UserRead(id=id, name=name )

async def service_delete_user(*, db: AsyncSession, id: int):
  user = await crud_get_user_by_id(db=db, id=id)

  if not user:
    raise NotFoundError("The user you want to delete doesn't exist.")
  if not user.is_active:
    raise BusinessLogicError("The user has already been deactivated previously.")

  await crud_delete_user(db=db, id=id)

  return

async def service_get_all_users(
  *,
  db: AsyncSession,
  page: int,
  filters: UserFilters
) -> Pagination:
  user_availables_filters = [
    FilterFactory.boolean(
      name=UserFilterNames.ACTIVE.value,
      label=UserFilterLabels.ACTIVE.value,
      current=filters.active_filter
    ),
    FilterFactory.boolean(
      name=UserFilterNames.ADMIN.value,
      label=UserFilterLabels.ADMIN.value,
      current=filters.admin_filter
    )
  ]

  result = await crud_get_all_users(db=db, page=page, filters=filters)

  pagination = get_pagination(pagination=result, page=page, available_filters=user_availables_filters)

  return pagination
