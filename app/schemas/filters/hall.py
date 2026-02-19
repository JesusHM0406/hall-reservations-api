from pydantic import BaseModel, Field


class HallFilters(BaseModel):
  available_filter: bool | None = Field(None)
