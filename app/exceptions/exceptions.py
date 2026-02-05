from app.exceptions.base import AppError

class NotFoundError(AppError):
  def __init__(self, message: str = "Resource not found"):
    super().__init__(message, status_code=404, code="NOT_FOUND")

class BusinessLogicError(AppError):
  def __init__(self, message: str):
    super().__init__(message, status_code=400, code="BUSINESS_RULE_VIOLATION")

class ConflictError(AppError):
  def __init__(self, message: str):
    super().__init__(message, status_code=409, code="RESOURCE_CONFLICT")
