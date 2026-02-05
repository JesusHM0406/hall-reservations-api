from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.hall import router as hall_router
from app.api.v1.routes.reservation import router as reservation_router
from app.core.config import settings
from app.exceptions.base import AppError

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
  return JSONResponse(
    status_code=exc.status_code,
    content={
      "status": "error",
      "code": exc.code,
      "message": exc.message,
      "path": request.url.path
    }
  )

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
  return JSONResponse(
    status_code=status.HTTP_409_CONFLICT,
    content={
      "status": "error",
      "code": "DATABASE_INTEGRITY_ERROR",
      "message": "Data integrity conflict (possible duplicate record).",
      "path": request.url.path
    }
  )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
  # I need to log the error
  return JSONResponse(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    content={
      "status": "error",
      "code": "INTERNAL_SERVER_ERROR",
      "message": "An unexpected error has occurred on the server.",
      "path": request.url.path
    }
  )

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(hall_router, prefix="/halls", tags=["Halls"])
app.include_router(reservation_router, prefix="/reservations", tags=["Reservations"])
