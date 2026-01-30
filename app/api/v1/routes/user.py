from fastapi import APIRouter, HTTPException
from app.api.deps import DBDep
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user
from app.models.user import User as User
from app.models.reservation import Reservation as Reservation
from app.models.hall import Hall as Hall

router = APIRouter()

@router.post("/")
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
  try:
    result = await create_user(db, user.name, user.password, user.password_confirm)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"{e}")

  return UserRead(id=result["id"], name=result["name"])
