from typing import TYPE_CHECKING, Any, List

from sqlalchemy import Boolean, Computed, FetchedValue, Index, Integer, String, event
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.engine import Connection
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import Table
from sqlalchemy.sql.type_api import TypeEngine

from app.db.base_class import Base

if TYPE_CHECKING:
  from app.models.reservation import Reservation

class Hall(Base):
  __tablename__ = "halls"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  description: Mapped[str] = mapped_column(String(1000), nullable=False)
  is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  search_vector: Mapped[TSVECTOR] = mapped_column(
    TSVECTOR,
    nullable=True,
    server_default=FetchedValue(),
    server_onupdate=FetchedValue()
  )
  # Relationships
  reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="hall", lazy="raise")

  __table_args__ = (
      Index("idx_room_search_vector", "search_vector", postgresql_using="gin"),
      Index("idx_room_name_trgm", "name", postgresql_using="gist", postgresql_ops={"name": "gist_trgm_ops"}),
    )

@event.listens_for(Hall.__table__, "before_create")
def add_computed_column(target: Table, connection: Connection, **kw: Any) -> None:
  # When testing with SQLite, we don't want to calculate this column because
  # SQLite doesn't have those functions, so we omit those calculations
  if connection.dialect.name != "sqlite":
    # If the dialect is not sqlite, then it is postgresql which, of course,
    # has those functions and therefore we can calculate this column.
    target.c.search_vector.server_default = Computed(
      "setweight(to_tsvector('english', name), 'A') || "
      "setweight(to_tsvector('english', description), 'B')",
      persisted=True
    )

@compiles(TSVECTOR, "sqlite")
def compile_tsvector_sqlite(type_: TypeEngine[Any], compiler: Any, **kw: Any) -> str:
  return "TEXT"
