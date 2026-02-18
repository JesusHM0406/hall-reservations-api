import math

from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.utils.filters_metadata import UserFilterNames
from app.utils.pagination_crud import PaginationCRUD
from app.schemas.user import UserComplete
from app.models.user_role import UserRole


async def crud_create_new_user(db: AsyncSession, name: str, pw_hash: str):
  new_user = User(name=name, pw_hash=pw_hash)
  db.add(new_user)
  return new_user

async def crud_get_user_by_id(db: AsyncSession, id: int):
  result = await db.execute(select(User).where(User.id == id))
  return result.scalar_one_or_none()

async def crud_update_user(db: AsyncSession, name: str, id: int):
  await db.execute(update(User).where(User.id == id).values(name=name))
  return

async def crud_delete_user(db: AsyncSession, id: int):
  await db.execute(delete(User).where(User.id == id))

async def crud_get_user_by_name(db: AsyncSession, name: str):
  result = await db.execute(select(User).where(User.name == name))
  return result.scalar_one_or_none()

async def crud_get_all_users(db: AsyncSession, page: int, filters: dict) -> PaginationCRUD:
  stmt = select(User).order_by(User.id.desc())
  total_records_stmt = select(func.count()).select_from(User)

  active_filter = filters.get(UserFilterNames.ACTIVE.value)
  admin_filter = filters.get(UserFilterNames.ADMIN.value)

  if active_filter is not  None:
    stmt = stmt.where(User.is_active == active_filter)
    total_records_stmt = total_records_stmt.where(User.is_active == active_filter)
  if admin_filter is not None:
    stmt = stmt.where(User.role == (UserRole.ADMIN if admin_filter else UserRole.USER))
    total_records_stmt = total_records_stmt.where(User.role == (UserRole.ADMIN if admin_filter else UserRole.USER))

  total_res = await db.execute(total_records_stmt)
  total_records = total_res.scalar() or 0

  pages = math.ceil(total_records / settings.PAGINATION_LIMIT_PER_PAGE) if total_records > 0 else 1

  current_page = max(1, min(page, pages))

  current_offset = (current_page - 1) * settings.PAGINATION_LIMIT_PER_PAGE

  stmt = stmt.limit(settings.PAGINATION_LIMIT_PER_PAGE).offset(current_offset)

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

  return PaginationCRUD(items=list(data), total=total_records, per_page=settings.PAGINATION_LIMIT_PER_PAGE, pages=pages, current_page=current_page)
