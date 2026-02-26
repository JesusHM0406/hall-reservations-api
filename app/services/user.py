from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.messages import ErrorMessages
from app.core.security import get_password_hash
from app.crud.user import (
  crud_count_superadmins,
  crud_create_new_user,
  crud_delete_user,
  crud_get_all_users,
  crud_get_user_by_id,
  crud_get_user_by_name,
  crud_restore_user,
  crud_update_user,
)
from app.exceptions.exceptions import BusinessLogicError, ConflictError, ForbiddenError, NotFoundError
from app.models.user_role import UserRole
from app.schemas.filters.user import UserFilters, UserFilterLabels, UserFilterNames, UserRoleFilter, UserStatusFilter
from app.schemas.user import UserAdminUpdate, UserComplete, UserRead
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

  try:
    new_user = await crud_create_new_user(db=db, name=name, pw_hash=pw_hash)
  except IntegrityError:
    # This IntegrityError is most likely due to a violation of name uniqueness
    raise ConflictError(ErrorMessages.DUPLICATED_RESERVATION)

  await db.flush()

  return UserRead(id=new_user.id, name=new_user.name)

async def service_get_user_by_id(
  *,
  db: AsyncSession,
  id: int,
  admin: UserComplete
) -> UserComplete:
  user = await crud_get_user_by_id(db=db, id=id)

  if not user or user.is_deleted or (user.role == UserRole.SUPERADMIN and admin.role != UserRole.SUPERADMIN):
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active,
    is_deleted=user.is_deleted
  )

async def service_update_user(
  *,
  db: AsyncSession,
  name: str,
  id: int
) -> UserRead:
  user = await crud_get_user_by_id(db=db, id=id)

  if not user or user.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

  name = name.strip()
  if not name:
    raise BusinessLogicError(ErrorMessages.EMPTY_NAME)

  existing_user = await crud_get_user_by_name(db=db, name=name)

  if existing_user and existing_user.id != id:
    raise ConflictError(ErrorMessages.DUPLICATED_USERNAME)

  await crud_update_user(user=user, name=name)

  return UserRead(id=id, name=name)

async def service_update_user_as_admin(
  *,
  db: AsyncSession,
  update: UserAdminUpdate,
  id: int,
  admin: UserComplete
) -> UserComplete:
  user = await crud_get_user_by_id(db=db, id=id)

  is_superadmin = admin.role == UserRole.SUPERADMIN

  if not user or user.is_deleted or (user.role == UserRole.SUPERADMIN and not is_superadmin):
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  if user.role == UserRole.ADMIN and not is_superadmin:
    raise BusinessLogicError(ErrorMessages.CANNOT_UPDATE_ADMIN)

  if user.id == admin.id:
    raise BusinessLogicError(ErrorMessages.CANNOT_UPDATE)

  if update.name:
    update.name = update.name.strip()

    if not update.name:
      raise BusinessLogicError(ErrorMessages.EMPTY_NAME)

    existing_user = await crud_get_user_by_name(db=db, name=update.name)

    if existing_user and existing_user.id != id:
      raise ConflictError(ErrorMessages.DUPLICATED_USERNAME)

  if update.is_active is False and user.role == UserRole.SUPERADMIN and admin.role == UserRole.SUPERADMIN:
    superadmin_count = await crud_count_superadmins(db=db)
    if superadmin_count == 1:
      raise BusinessLogicError(ErrorMessages.DISABLE_LAST_SUPERADMIN)

  if not is_superadmin and update.role is not None:
    raise ForbiddenError(ErrorMessages.NOT_ENOUGH_PERMISSIONS_UPDATE_ROLE)

  updated_user = await crud_update_user(
    user=user,
    name=update.name,
    role=update.role,
    is_active=update.is_active
  )

  return UserComplete(
    id=id,
    name=updated_user.name,
    role=updated_user.role,
    is_active=updated_user.is_active,
    is_deleted=updated_user.is_deleted
  )

async def service_delete_current_user(*, db: AsyncSession, id: int, current_user: UserComplete):
  user = await crud_get_user_by_id(db=db, id=id)

  if not user or user.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  if current_user.role == UserRole.SUPERADMIN:
    superadmin_count = await crud_count_superadmins(db=db)
    if superadmin_count == 1:
      raise BusinessLogicError(ErrorMessages.DELETE_LAST_SUPERADMIN)

  await crud_delete_user(user=user)

  return

async def service_delete_user_as_admin(*, db: AsyncSession, id_delete: int, admin: UserComplete):
  user = await crud_get_user_by_id(db=db, id=id_delete)

  if not user or user.is_deleted or (user.role == UserRole.SUPERADMIN and admin.role != UserRole.SUPERADMIN):
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  if user.id == admin.id:
    raise BusinessLogicError(ErrorMessages.DELETE_CURRENT_ADMIN)

  if user.role == UserRole.ADMIN and admin.role != UserRole.SUPERADMIN:
    raise BusinessLogicError(ErrorMessages.CANNOT_DELETE_ADMIN)

  if user.role == UserRole.SUPERADMIN and admin.role == UserRole.SUPERADMIN:
    superadmin_count = await crud_count_superadmins(db=db)
    if superadmin_count == 1:
      raise BusinessLogicError(ErrorMessages.DELETE_LAST_SUPERADMIN)

  await crud_delete_user(user=user)

  return

async def service_restore_user(
  *,
  db: AsyncSession,
  id: int,
  new_name: str,
  admin: UserComplete
) -> UserComplete:
  user = await crud_get_user_by_id(db=db, id=id)

  if not user or (user.role == UserRole.SUPERADMIN and admin.role != UserRole.SUPERADMIN):
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  if user.is_deleted is False:
    raise ConflictError(ErrorMessages.USER_ALREADY_ACTIVE)

  if user.role == UserRole.ADMIN and admin.role != UserRole.SUPERADMIN:
    raise BusinessLogicError(ErrorMessages.CANNOT_RESTORE_ADMIN)

  new_name = new_name.strip()
  if not new_name:
    raise BusinessLogicError(ErrorMessages.EMPTY_NAME)

  existing_user = await crud_get_user_by_name(db=db, name=new_name)

  if existing_user:
    raise ConflictError(ErrorMessages.DUPLICATED_USERNAME)

  await crud_restore_user(user=user, new_name=new_name)

  return UserComplete(
    id=user.id,
    name=user.name,
    role=user.role,
    is_active=user.is_active,
    is_deleted=user.is_deleted
  )

async def service_get_all_users(
  *,
  db: AsyncSession,
  page: int,
  filters: UserFilters,
  admin: UserComplete
) -> Pagination:
  user_role_filter_dict: dict[str, str] = {}

  for role in UserRoleFilter:
    user_role_filter_dict[role.value] = role.value.capitalize()

  if admin.role != UserRole.SUPERADMIN:
    del user_role_filter_dict[UserRoleFilter.SUPERADMIN]
    if filters.role == UserRoleFilter.SUPERADMIN:
      filters.role = None

  user_status_filter_dict: dict[str, str] = {}

  for status in UserStatusFilter:
    user_status_filter_dict[status.value] = status.value.capitalize().replace("_", " ")

  user_availables_filters = [
    FilterFactory.select(
      name=UserFilterNames.ROLE.value,
      label=UserFilterLabels.ROLE.value,
      options=user_role_filter_dict,
      current=filters.role
    ),
    FilterFactory.select(
      name=UserFilterNames.STATUS.value,
      label=UserFilterLabels.STATUS.value,
      options=user_status_filter_dict,
      current=filters.status
    )
  ]

  result = await crud_get_all_users(db=db, page=page, filters=filters, admin=admin)

  pagination = get_pagination(pagination=result, page=page, available_filters=user_availables_filters)

  return pagination
