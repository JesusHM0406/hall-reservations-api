import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.hall import router as hall_router
from app.api.v1.routes.reservation import router as reservation_router
from app.api.v1.routes.user import router as user_router
from app.core.config import settings
from app.core.messages import ErrorMessages
from app.exceptions.base import AppError
from app.middleware.rate_limit import GlobalRateLimitMiddleware
from app.utils.tasks import clean_expired_reservations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("Starting worker for reservation cleaning...")
  task = asyncio.create_task(clean_expired_reservations())

  yield

  logger.info("Canceling background tasks...")
  task.cancel()
  try:
    await task
  except asyncio.CancelledError:
    logger.info("Worker stopped cleanly.")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

# Global rate limiting middleware
app.add_middleware(GlobalRateLimitMiddleware)

@app.get("/health", tags=["Health"])
async def health_check():
  """Health check endpoint for Docker and monitoring."""
  return {"status": "ok", "detail": "API is running"}

@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
  return JSONResponse(
    status_code=exc.status_code,
    content={
      "status": "error",
      "code": exc.code,
      "detail": exc.detail,
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
      "detail": ErrorMessages.INTEGRITY_ERROR,
      "path": request.url.path
    }
  )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
  logger.error(f"Unhandled error in {request.url.path}: {str(exc)}", exc_info=True)
  return JSONResponse(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    content={
      "status": "error",
      "code": "INTERNAL_SERVER_ERROR",
      "detail": ErrorMessages.UNEXPECTED_ERROR,
      "path": request.url.path
    }
  )

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(hall_router, prefix="/halls", tags=["Halls"])
app.include_router(reservation_router, prefix="/reservations", tags=["Reservations"])
