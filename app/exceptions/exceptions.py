from app.core.messages import ErrorMessages
from app.exceptions.base import AppError

class NotFoundError(AppError):
  def __init__(self, detail: str = ErrorMessages.RESOURCE_NOT_FOUND):
    super().__init__(detail, status_code=404, code="NOT_FOUND")

class BusinessLogicError(AppError):
  def __init__(self, detail: str):
    super().__init__(detail, status_code=400, code="BUSINESS_RULE_VIOLATION")

class ConflictError(AppError):
  def __init__(self, detail: str):
    super().__init__(detail, status_code=409, code="RESOURCE_CONFLICT")

class ForbiddenError(AppError):
  def __init__(self, detail: str):
    super().__init__(detail, status_code=403, code="NOT_ENOUGH_PERMISSIONS")
