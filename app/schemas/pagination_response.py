from pydantic import BaseModel, ConfigDict, computed_field
from typing import List, Any

class PaginationResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

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
  def next_num(self) -> int | None:
    return self.current_page + 1 if self.has_next else None

  @computed_field
  def prev_num(self) -> int | None:
    return self.current_page - 1 if self.has_prev else None
