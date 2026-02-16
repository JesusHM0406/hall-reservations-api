from dataclasses import dataclass
from typing import Any, List

from app.utils.pagination_crud import PaginationCRUD


@dataclass
class Pagination:
  items: List[Any]
  requested_page: int
  per_page: int
  total: int
  pages: int
  current_page: int

def get_pagination(pagination: PaginationCRUD, page: int) -> Pagination:
  return Pagination(items=pagination.items, requested_page=page, per_page=pagination.per_page, total=pagination.total, pages=pagination.pages, current_page=pagination.current_page)
