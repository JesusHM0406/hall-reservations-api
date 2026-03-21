from enum import Enum
from pydantic import BaseModel, Field


class HallStatusFilter(str, Enum):
  AVAILABLE = "available"
  UNAVAILABLE = "unavailable"
  ALL = "all"

class HallFilters(BaseModel):
  status: HallStatusFilter | None = Field(None)

class HallFilterNames(str, Enum):
  STATUS = "status"