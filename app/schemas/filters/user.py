from enum import Enum
from pydantic import BaseModel, Field

from app.models.user_role import UserRole


class UserRoleFilter(str, Enum):
  SUPERADMIN = UserRole.SUPERADMIN.value
  ADMIN = UserRole.ADMIN.value
  USER = UserRole.USER.value
  ALL = "all"

class UserStatusFilter(str, Enum):
  ACTIVE = "active"
  INACTIVE = "inactive"
  DELETED = "deleted"
  NOT_DELETED = "not_deleted"
  ALL = "all"

class UserFilters(BaseModel):
  role: UserRoleFilter | None = Field(None)
  status: UserStatusFilter | None = Field(None)

class UserFilterNames(str, Enum):
  ROLE = "role"
  STATUS = "status"

class UserFilterLabels(str, Enum):
  ROLE = "By role"
  STATUS = "By status"
