from enum import Enum

class ReservationStatus(str, Enum):
  CONFIRMED = "confirmed"
  CANCELLED = "cancelled"
  FINISHED = "finished"
