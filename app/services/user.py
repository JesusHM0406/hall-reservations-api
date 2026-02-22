from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.messages import ErrorMessages
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
from app.schemas.filters.user import UserFilters, UserFilterLabels, UserFilterNames, UserRoleFilter, UserStatusFilter
from app.schemas.user import UserComplete, UserRead
from app.utils.pagination import Pagination, get_pagination
from app.utils.pagination_filters import FilterFactory

async def service_create_user(
  *,
  db: AsyncSession,
  name: str,
  password: str,
  password_confirm: str
) -> UserRead:
  if len(password) < settings.MIN_PASSWORD_SIZE:
    raise BusinessLogicError(ErrorMessages.SHORT_PASSWORD)
  if password != password_confirm:
    raise BusinessLogicError(ErrorMessages.PASSWORDS_MISMATCH)

  name = name.strip()
  if not name:
    raise BusinessLogicError(ErrorMessages.EMPTY_NAME)

  user = await crud_get_user_by_name(db=db, name=name)

  if user is not None:
    raise ConflictError(ErrorMessages.DUPLICATED_USERNAME)

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
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

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
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

  existing_user = await crud_get_user_by_name(db=db, name=name)

  if existing_user:
    raise ConflictError(ErrorMessages.DUPLICATED_USERNAME)

  await crud_update_user(db=db, name=name, id=id)

  return UserRead(id=id, name=name )

async def service_delete_user(*, db: AsyncSession, id: int):
  user = await crud_get_user_by_id(db=db, id=id)

  if not user:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

  await crud_delete_user(db=db, user=user)

  return

async def service_get_all_users(
  *,
  db: AsyncSession,
  page: int,
  filters: UserFilters
) -> Pagination:
  user_role_filter_dict: dict[str, str] = {}

  for status in UserRoleFilter:
    user_role_filter_dict[status.value] = status.value.capitalize()

  user_status_filter_dict: dict[str, str] = {}

  for status in UserStatusFilter:
    user_status_filter_dict[status.value] = status.value.capitalize()

  user_availables_filters = [
    FilterFactory.select(
      name=UserFilterNames.STATUS.value,
      label=UserFilterLabels.STATUS.value,
      options=user_role_filter_dict,
      current=filters.status
    ),
    FilterFactory.select(
      name=UserFilterNames.ROLE.value,
      label=UserFilterLabels.ROLE.value,
      options=user_status_filter_dict,
      current=filters.role
    )
  ]

  result = await crud_get_all_users(db=db, page=page, filters=filters)

  pagination = get_pagination(pagination=result, page=page, available_filters=user_availables_filters)

  return pagination
