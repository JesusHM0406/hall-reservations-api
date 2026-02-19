from enum import Enum
from pydantic import BaseModel, Field


class HallFilters(BaseModel):
  available_filter: bool | None = Field(None)

class HallFilterNames(str, Enum):
  AVAILABLE = "available_filter"

class HallFilterLabels(str, Enum):
  AVAILABLE = "Only available halls"
