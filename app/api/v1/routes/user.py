from fastapi import APIRouter, HTTPException
from app.api.deps import DBDep
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user, get_user
from app.models.user import User as User
from app.models.reservation import Reservation as Reservation
from app.models.hall import Hall as Hall

router = APIRouter()

@router.post("/", status_code=201)
async def add_user(user: UserCreate, db: DBDep) -> UserRead:
  try:
    user_created = await create_user(db, user.name, user.password, user.password_confirm)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"{e}")

  return user_created

@router.get("/{id}")
async def get_user_by_id(id: int, db: DBDep) -> UserRead:
  try:
    user = await get_user(db, id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return user
