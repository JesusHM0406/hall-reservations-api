from enum import Enum

class UserFilterNames(str, Enum):
  ACTIVE = "active_filter"
  ADMIN = "admin_filter"

class UserFilterLabels(str, Enum):
  ACTIVE = "Only active users"
  ADMIN = "Only admins"

class HallFilterNames(str, Enum):
  AVAILABLE = "available_filter"

class HallFilterLabels(str, Enum):
  AVAILABLE = "Only available halls"

class ReservationFilterNames(str, Enum):
  ID = "filter_id"
  USER = "user_filter"
  HALL = "hall_filter"

class ReservationFilterLabels(str, Enum):
  USER = "Filter by user id"
  HALL = "Filter by hall id"
