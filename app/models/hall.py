from db.base_class import Base
from sqlalchemy import Integer, String, Boolean, Text as SQLtext
from sqlalchemy.orm import Mapped, mapped_column
from typing import Text

class User(Base):
  __tablename__ = "halls"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
  description: Mapped[Text] = mapped_column(SQLtext, nullable=False)
  is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)