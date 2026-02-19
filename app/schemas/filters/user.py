from pydantic import BaseModel, Field


class UserFilters(BaseModel):
  active_filter: bool | None = Field(None)
  admin_filter: bool | None = Field(None)
