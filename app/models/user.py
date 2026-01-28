from db.base_class import Base
from models.user_role import UserRole
from sqlalchemy import Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
  __tablename__ = "users"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
  pw_hash: Mapped[str] = mapped_column(String(255), nullable=False)
  role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), server_default=UserRole.USER, nullable=False)