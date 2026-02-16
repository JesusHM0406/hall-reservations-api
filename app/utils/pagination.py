import math
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Pagination:
  items: List[Any]
  page: int
  per_page: int
  total: int

  pages: int = field(init=False)
  current_page: int = field(init=False)

  def __post_init__(self):
    self.pages = math.ceil(self.total / self.per_page) if self.total > 0 else 1

    self.current_page = max(1, min(self.page, self.pages))
