from enum import Enum

class ReservationStatus(str, Enum):
  PENDING = "pending"
  CONFIRMED = "confirmed"
  CANCELLED = "cancelled"
  EXPIRED = "expired"
  FINISHED = "finished"