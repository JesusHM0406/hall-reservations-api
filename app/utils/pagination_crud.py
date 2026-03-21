from dataclasses import dataclass
from typing import List, Generic

from app.utils.generic_type import T


@dataclass
class PaginationCRUD(Generic[T]):
  items: List[T]
  total: int
  per_page: int
  pages: int
  current_page: int
