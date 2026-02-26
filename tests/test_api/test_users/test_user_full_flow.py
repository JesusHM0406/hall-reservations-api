
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserAdminUpdate, UserCreate, UserRestoreUpdate, UserUpdate


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

async def test_hierarchy_and_escalation_real_flow(client: AsyncClient, db_session: AsyncSession):
  # 1: Superadmin creation (in db directly)
  superadmin_pw = "SecretSuperAdmin123!"
  superadmin_hash = get_password_hash(password=superadmin_pw)

  superadmin = User(name="superadmin", pw_hash=superadmin_hash, role=UserRole.SUPERADMIN, is_active=True, is_deleted=False)
  db_session.add(superadmin)

  superadmin_login_data = {
    "username":superadmin.name,
    "password":superadmin_pw
  }

  response = await client.post("/auth/login", data=superadmin_login_data)
  assert response.status_code == 200

  superadmin_token_class = response.json()
  superadmin_token = superadmin_token_class["access_token"]

  await db_session.flush()

  # 2: Normal user (future admin promotion)
  user_scheme = UserCreate(
    name="Karl Marx",
    password="password",
    password_confirm="password"
  )

  response = await client.post("/users/", json=user_scheme.model_dump())
  assert response.status_code == 201

  await db_session.flush()

  login_data = {
    "username":user_scheme.name,
    "password":user_scheme.password
  }

  response = await client.post("/auth/login", data=login_data)
  assert response.status_code == 200

  user_token_class = response.json()
  user_token = user_token_class["access_token"]

  response = await client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
  assert response.status_code == 200

  user_id = response.json()["id"]

  new_superadmin_name = "New Superadmin Name"
  superadmin_update = UserAdminUpdate(
    name=new_superadmin_name,
    role=None,
    is_active=None
  )

  response = await client.patch(
    f"/users/{superadmin.id}",
    headers={"Authorization": f"Bearer {user_token}"},
    json=superadmin_update.model_dump()
  )

  assert response.status_code == 403
  assert response.json()["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  # 3: Superadmin promotes normal user to admin
  user_update = UserAdminUpdate(
    name=None,
    role=UserRole.ADMIN,
    is_active=None
  )

  await db_session.flush()

  assert user_id != superadmin.id

  response = await client.patch(
    f"/users/{user_id}",
    headers={"Authorization": f"Bearer {superadmin_token}"},
    json=user_update.model_dump()
  )

  assert response.status_code == 200

  await db_session.flush()

  admin = await db_session.get(User, user_id)

  assert admin is not None
  assert admin.role == UserRole.ADMIN

  response = await client.patch(
    f"/users/{superadmin.id}",
    headers={"Authorization": f"Bearer {user_token}"},
    json=superadmin_update.model_dump()
  )

  # The administrator can now update user information, but cannot yet update super administrator information.
  assert response.status_code == 404
  assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

  admin_token = user_token

  # 4: New user (the admin will try to promote this user)
  user2_scheme = UserCreate(
    name="Spinoza",
    password="password",
    password_confirm="password"
  )

  response = await client.post("/users/", json=user2_scheme.model_dump())
  assert response.status_code == 201

  await db_session.flush()

  login_data2 = {
    "username":user2_scheme.name,
    "password":user2_scheme.password
  }

  response = await client.post("/auth/login", data=login_data2)
  assert response.status_code == 200

  user2_token_class = response.json()
  user2_token = user2_token_class["access_token"]

  response = await client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
  assert response.status_code == 200

  user2_id = response.json()["id"]

  # 5: Admin tries to promote user to admin
  user_update = UserAdminUpdate(
    name=None,
    role=UserRole.ADMIN,
    is_active=None
  )

  response = await client.patch(
    f"/users/{user2_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=user_update.model_dump()
  )

  assert response.status_code == 403
  assert response.json()["message"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS_UPDATE_ROLE

  # 6: Superadmin promotes admin to superadmin
  admin_update = UserAdminUpdate(
    name=None,
    role=UserRole.SUPERADMIN,
    is_active=None
  )

  response = await client.patch(
    f"/users/{admin.id}",
    headers={"Authorization": f"Bearer {superadmin_token}"},
    json=admin_update.model_dump()
  )

  assert response.status_code == 200

  await db_session.flush()

  new_superadmin = await db_session.get(User, admin.id)

  assert new_superadmin is not None
  assert new_superadmin.role == UserRole.SUPERADMIN

  new_superadmin_token = admin_token
  # 7: The user who has been promoted to admin and then to
  # super administrator can now edit the superadmin data
  response = await client.patch(
    f"/users/{superadmin.id}",
    headers={"Authorization": f"Bearer {new_superadmin_token}"},
    json=superadmin_update.model_dump()
  )

  assert response.status_code == 200

  await db_session.flush()

  superadmin_updated_db = await db_session.get(User, superadmin.id)

  assert superadmin_updated_db is not None
  assert superadmin_updated_db.name == new_superadmin_name
