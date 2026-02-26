
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserRestoreUpdate, UserUpdate


async def test_user_complete_lifecycle(client: AsyncClient, db_session: AsyncSession):
  # 1: Creation
  user_scheme = UserCreate(
    name="Karl Marx",
    password="password",
    password_confirm="password"
  )

  response = await client.post("/users/", json=user_scheme.model_dump())
  assert response.status_code == 201

  await db_session.flush()

  # 1.5: Login
  login_data = {
    "username":user_scheme.name,
    "password":user_scheme.password
  }

  response = await client.post("/auth/login", data=login_data)
  assert response.status_code == 200

  user_token_class = response.json()
  user_token = user_token_class["access_token"]

  # 2: Self-management
  response = await client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
  assert response.status_code == 200
  data = response.json()

  assert data["id"] is not None
  assert data["name"] == user_scheme.name

  user_update = UserUpdate(name="Karl Marx Jr.")
  response = await client.patch("/users/me", headers={"Authorization": f"Bearer {user_token}"}, json=user_update.model_dump())
  assert response.status_code == 200

  data = response.json()

  assert data["id"] is not None
  assert data["name"] == user_update.name

  user_scheme.name = data["name"]
  user_id = data["id"]

  # 3: Conflict
  new_user_scheme = UserCreate(
    name="New User",
    password="password123",
    password_confirm="password123"
  )

  response = await client.post("/users/", json=new_user_scheme.model_dump())
  assert response.status_code == 201
  new_user_id = response.json()["id"]

  await db_session.flush()

  user_update = UserUpdate(name=new_user_scheme.name)

  response = await client.patch("/users/me", headers={"Authorization": f"Bearer {user_token}"}, json=user_update.model_dump())
  assert response.status_code == 409
  assert response.json()["message"] == ErrorMessages.DUPLICATED_USERNAME

  response = await client.patch(f"/users/{new_user_id}", headers={"Authorization": f"Bearer {user_token}"})
  assert response.status_code == 403
  assert response.json()["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  # 4: Self delete
  response = await client.delete("/users/me", headers={"Authorization": f"Bearer {user_token}"})
  assert response.status_code == 204

  response = await client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
  assert response.status_code == 404
  assert response.json()["detail"] == ErrorMessages.USER_NOT_FOUND

  # 5: Admin intervention
  admin_pw = "SecretAdmin123!"
  admin_hash = get_password_hash(password=admin_pw)

  admin = User(name="admin", pw_hash=admin_hash, role=UserRole.ADMIN, is_active=True, is_deleted=False)
  db_session.add(admin)

  admin_login_data = {
    "username":admin.name,
    "password":admin_pw
  }

  response = await client.post("/auth/login", data=admin_login_data)
  assert response.status_code == 200

  admin_token_class = response.json()
  admin_token = admin_token_class["access_token"]

  await db_session.flush()

  response = await client.get(f"/users/{new_user_id}", headers={"Authorization": f"Bearer {admin_token}"})
  assert response.status_code == 200
  assert response.json()["name"] == new_user_scheme.name

  response = await client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
  assert response.status_code == 404
  assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

  # 6: Restore
  restore_scheme = UserRestoreUpdate(name="Karl Marx Return")
  response = await client.patch(
    f"/users/{user_id}/restore",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=restore_scheme.model_dump()
  )
  assert response.status_code == 200

  await db_session.flush()

  user = await db_session.get(User, user_id)

  assert user is not None
  assert user.id == user_id # Just to make sure i haven't made any mistakes
  assert user.is_deleted is False

  response = await client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
  assert response.status_code == 200
  assert response.json()["name"] == restore_scheme.name
