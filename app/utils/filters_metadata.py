from enum import Enum

class UserFilterNames(str, Enum):
  ACTIVE = "active_filter"
  ADMIN = "admin_filter"

class UserFilterLabels(str, Enum):
  ACTIVE = "Only active users"
  ADMIN = "Only admins"
