from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

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

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(hall_router, prefix="/halls", tags=["Halls"])
app.include_router(reservation_router, prefix="/reservations", tags=["Reservations"])
