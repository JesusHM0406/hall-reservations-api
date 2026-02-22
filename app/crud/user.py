from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.filters.user import UserFilters, UserRoleFilter, UserStatusFilter
from app.utils.pagination import get_pagination_computed_fields
from app.utils.pagination_crud import PaginationCRUD
from app.schemas.user import UserComplete
from app.models.user_role import UserRole


async def crud_create_new_user(*, db: AsyncSession, name: str, pw_hash: str):
  new_user = User(name=name, pw_hash=pw_hash)
  db.add(new_user)
  return new_user

async def crud_get_user_by_id(*, db: AsyncSession, id: int):
  result = await db.execute(select(User).where(User.id == id))
  return result.scalar_one_or_none()

async def crud_update_user(
  *,
  user: User,
  name: str | None = None,
  role: UserRole | None = None,
  is_active: bool | None = None
):
  if name:
    user.name = name
  if role:
    user.role = role
  if is_active is not None:
    user.is_active = is_active

  return user

async def crud_delete_user(*, db: AsyncSession, user: User):
  user.is_active = False

async def crud_get_user_by_name(*, db: AsyncSession, name: str):
  result = await db.execute(select(User).where(User.name == name))
  return result.scalar_one_or_none()

async def crud_get_all_users(
  *,
  db: AsyncSession,
  page: int,
  filters: UserFilters
) -> PaginationCRUD:
  stmt = select(User).order_by(User.id.desc())
  total_records_stmt = select(func.count()).select_from(User)

  filters_to_apply = []

  status_filter = filters.status
  role_filter = filters.role

  if status_filter == UserStatusFilter.ACTIVE:
    filters_to_apply.append(User.is_active.is_(True))
  elif status_filter == UserStatusFilter.INACTIVE:
    filters_to_apply.append(User.is_active.is_(False))

  if role_filter == UserRoleFilter.ADMIN:
    filters_to_apply.append(User.role == UserRole.ADMIN)
  elif role_filter == UserRoleFilter.USER:
    filters_to_apply.append(User.role == UserRole.USER)

  for condition in filters_to_apply:
    stmt = stmt.where(condition)
    total_records_stmt = total_records_stmt.where(condition)

  total_res = await db.execute(total_records_stmt)
  total_records = total_res.scalar() or 0

  computed_fields = get_pagination_computed_fields(
    total_records=total_records,
    page=page
  )

  stmt = stmt.limit(settings.PAGINATION_LIMIT_PER_PAGE).offset(computed_fields.current_offset)

  result = await db.execute(stmt)
  result_items = result.scalars().all()
  data = [
    UserComplete(
      id=user.id,
      name=user.name,
      role=user.role,
      is_active=user.is_active
    )
    for user in result_items
  ]

  return PaginationCRUD(
    items=list(data),
    total=total_records,
    per_page=settings.PAGINATION_LIMIT_PER_PAGE,
    pages=computed_fields.pages,
    current_page=computed_fields.current_page
  )
