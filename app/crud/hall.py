from typing import Any, Sequence

from sqlalchemy import func, or_, select, case
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.config import settings
from app.models.hall import Hall
from app.schemas.filters.hall import HallFilters, HallStatusFilter
from app.schemas.hall import HallRead
from app.utils.pagination import get_pagination_computed_fields
from app.utils.pagination_crud import PaginationCRUD


async def crud_create_new_hall(
  *,
  db: AsyncSession,
  name: str,
  description: str,
  is_available: bool
):
  new_hall = Hall(
    name=name,
    description=description,
    is_available=is_available
  )
  db.add(new_hall)
  return new_hall

async def crud_get_hall_by_id(*, db: AsyncSession, id: int):
  result = await db.execute(select(Hall).where(Hall.id == id))
  return result.scalar_one_or_none()

async def crud_get_hall_by_name(*, db: AsyncSession, name: str):
  result = await db.execute(select(Hall).where(Hall.name == name))
  return result.scalar_one_or_none()

async def crud_update_hall(
  *,
  hall: Hall,
  name: str | None,
  description: str | None,
  is_available: bool | None
):
  if name is not None:
    hall.name = name
  if description is not None:
    hall.description = description
  if is_available is not None:
    hall.is_available = is_available

  return hall

async def crud_update_hall_availability(*, hall: Hall, is_available: bool):
  hall.is_available = is_available

  return hall

async def crud_get_all_halls(
  *,
  db: AsyncSession,
  page: int,
  filters: HallFilters
) -> PaginationCRUD[HallRead]:
  stmt = select(Hall).order_by(Hall.id.desc())
  total_records_stmt = select(func.count()).select_from(Hall)

  filters_to_apply: list[ColumnElement[bool]] = []

  status_filter = filters.status

  if status_filter == HallStatusFilter.AVAILABLE:
    filters_to_apply.append(Hall.is_available.is_(True))
  elif status_filter == HallStatusFilter.UNAVAILABLE:
    filters_to_apply.append(Hall.is_available.is_(False))

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
    HallRead(
      id=hall.id,
      name=hall.name,
      description=hall.description,
      is_available=hall.is_available
    )
    for hall in result_items
  ]

  return PaginationCRUD(
    items=list(data),
    total=total_records,
    per_page=settings.PAGINATION_LIMIT_PER_PAGE,
    pages=computed_fields.pages,
    current_page=computed_fields.current_page
  )

async def crud_search_halls(*, db: AsyncSession, search_query: str) -> Sequence[Row[tuple[int, str, bool, Any, Any]]]:
  query_str = search_query.strip().lower()
  if not query_str:
    return []

  ts_query = func.websearch_to_tsquery("english", query_str)

  relevance = (
    case((Hall.name.ilike(f"{query_str}%"), 2.0), else_=0.0) +
    func.similarity(Hall.name, query_str) * 1.5 +
    case((Hall.search_vector.op("@@")(ts_query), 1.0), else_=0.0) +
    func.similarity(Hall.description, query_str) * 0.5
  ).label("rank")

  stmt = (
    select(
      Hall.id,
      Hall.name,
      Hall.is_available,
      case(
        (func.char_length(Hall.description) > 100, func.left(Hall.description, 97) + "..."),
        else_=Hall.description
      ).label("preview"),
      relevance
    )
    .filter(
      or_(
        Hall.name.op("%")(query_str),
        Hall.search_vector.op("@@")(ts_query),
        Hall.name.ilike(f"%{query_str}%"),
        Hall.description.ilike(f"%{query_str}%"),
        func.similarity(Hall.name, query_str) > 0.2
      )
    )
    .order_by(relevance.desc())
    .limit(settings.SEARCH_LIMIT)
  )

  result = await db.execute(stmt)
  return result.all()
