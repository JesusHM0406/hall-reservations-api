from dataclasses import dataclass
from typing import Any, List


@dataclass
class Pagination:
  items: List[Any]
  requested_page: int
  per_page: int
  total: int
  pages: int
  current_page: int
