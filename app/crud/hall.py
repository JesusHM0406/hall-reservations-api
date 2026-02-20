from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.hall import Hall
from app.schemas.filters.hall import HallFilters
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
  if name:
    hall.name = name
  if description:
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
) -> PaginationCRUD:
  stmt = select(Hall).order_by(Hall.id.desc())
  total_records_stmt = select(func.count()).select_from(Hall)

  available_filter = filters.available_filter

  if available_filter is not None:
    stmt = stmt.where(Hall.is_available == available_filter)
    total_records_stmt = total_records_stmt.where(Hall.is_available == available_filter)

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

async def crud_search_halls(*, db: AsyncSession, search_query: str):
  query_str = search_query.strip().lower()
  if not query_str:
      return []

  formatted_fts = " & ".join(f"{word}:*" for word in query_str.split())
  ts_query = func.to_tsquery("english", formatted_fts)

  relevance = (
    func.ts_rank(Hall.search_vector, ts_query) +
    func.similarity(Hall.name, query_str) +
    (1.0 if query_str else 0.0)
  ).label("rank")

  stmt = (
    select(Hall, relevance)
    .filter(
      or_(
        Hall.search_vector.op("@@")(ts_query),
        Hall.name.op("%")(query_str),
        Hall.name.ilike(f"{query_str}%"),
        Hall.description.ilike(f"% {query_str}%")
      )
    )
    .order_by(relevance.desc())
    .limit(settings.SEARCH_LIMIT)
  )

  result = await db.execute(stmt)
  return result.all()
