from enum import Enum

class ReservationStatus(str, Enum):
  CONFIRMED = "confirmed"
  CANCELLED = "cancelled"
  EXPIRED = "expired"
  FINISHED = "finished"
