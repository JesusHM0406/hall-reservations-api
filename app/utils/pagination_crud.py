from dataclasses import dataclass
from typing import Any, List


@dataclass
class PaginationCRUD:
  items: List[Any]
  total: int
  per_page: int
  pages: int
  current_page: int
