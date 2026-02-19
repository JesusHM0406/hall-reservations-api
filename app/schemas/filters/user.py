from pydantic import BaseModel, Field


class UserFilters(BaseModel):
  active_filter: bool | None = Field(None)
  admin_filter: bool | None = Field(None)

class UserFilterNames(str, Enum):
  ACTIVE = "active_filter"
  ADMIN = "admin_filter"

class UserFilterLabels(str, Enum):
  ACTIVE = "Only active users"
  ADMIN = "Only admins"
