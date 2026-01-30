from fastapi import FastAPI

from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.hall import router as hall_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(hall_router, prefix="/halls", tags=["Halls"])
