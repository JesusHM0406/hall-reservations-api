from typing import Any, List

from pydantic import BaseModel, computed_field

from app.utils.pagination_crud import PaginationCRUD


class Pagination(BaseModel):
  items: List[Any]
  total: int
  requested_page: int
  per_page: int
  pages: int
  current_page: int

  @computed_field
  def has_prev(self) -> bool:
    return self.current_page > 1

  @computed_field
  def has_next(self) -> bool:
    return self.current_page < self.pages

  @computed_field
  def prev_num(self) -> int | None:
    return self.current_page - 1 if self.has_prev else None

  @computed_field
  def next_num(self) -> int | None:
    return self.current_page + 1 if self.has_next else None

def get_pagination(pagination: PaginationCRUD, page: int) -> Pagination:
  return Pagination(items=pagination.items, requested_page=page, per_page=pagination.per_page, total=pagination.total, pages=pagination.pages, current_page=pagination.current_page)
