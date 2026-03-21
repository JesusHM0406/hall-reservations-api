from dataclasses import dataclass
import math
from typing import Any, List

from pydantic import BaseModel, computed_field

from app.core.config import settings
from app.utils.pagination_crud import PaginationCRUD
from app.utils.pagination_filters import AvailableFilter


class Pagination(BaseModel):
  items: List[Any]
  total: int
  requested_page: int
  per_page: int
  pages: int
  current_page: int
  available_filters: List[AvailableFilter] = []

  @computed_field
  def has_prev(self) -> bool:
    return self.current_page > 1

  @computed_field
  def has_next(self) -> bool:
    return self.current_page < self.pages

@dataclass
class PaginationComputedFields():
  pages: int
  current_page: int
  current_offset: int

def get_pagination(*, pagination: PaginationCRUD, page: int, available_filters: List[AvailableFilter]) -> Pagination:
  return Pagination(
    items=pagination.items,
    requested_page=page,
    per_page=pagination.per_page,
    total=pagination.total,
    pages=pagination.pages,
    current_page=pagination.current_page,
    available_filters=available_filters
  )

def get_pagination_computed_fields(
  *,
  total_records: int,
  page: int
) -> PaginationComputedFields:
  pages = math.ceil(
    total_records / settings.PAGINATION_LIMIT_PER_PAGE
  ) if total_records > 0 else 1

  current_page = max(1, min(page, pages))

  current_offset = (current_page - 1) * settings.PAGINATION_LIMIT_PER_PAGE

  return PaginationComputedFields(
    pages=pages,
    current_page=current_page,
    current_offset=current_offset
  )
