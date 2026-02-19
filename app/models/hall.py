from app.db.base_class import Base
from sqlalchemy import Integer, String, Boolean, Text as SQLtext, Computed, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Text, TYPE_CHECKING, List

if TYPE_CHECKING:
  from app.models.reservation import Reservation

class Hall(Base):
  __tablename__ = "halls"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
  description: Mapped[Text] = mapped_column(SQLtext, nullable=False)
  is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  search_vector: Mapped[TSVECTOR] = mapped_column(
      TSVECTOR,
      Computed(
        "setweight(to_tsvector('english', name), 'A') || "
        "setweight(to_tsvector('english', description), 'B')",
        persisted=True
      )
    )

  # Relationships
  reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="hall", lazy="raise")

  __table_args__ = (
      Index("idx_room_search_vector", "search_vector", postgresql_using="gin"),
      Index("idx_room_name_trgm", "name", postgresql_using="gist", postgresql_ops={"name": "gist_trgm_ops"}),
    )
