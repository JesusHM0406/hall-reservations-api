from pydantic import BaseModel, Field


class ReservationFilters(BaseModel):
  user_id: int | None = Field(None, ge=1)
  hall_id: int | None = Field(None, ge=1)
  status: str | None = Field(None, pattern="^(confirmed|cancelled|finished|expired)$")
