from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.messages import ErrorMessages
from app.main import app
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserComplete, UserCreate, UserUpdate

class TestGetMe:
  async def test_get_me_success(self, client: AsyncClient):
    me_mock = UserComplete(
      id=123,
      name="Karl Marx",
      role=UserRole.USER,
      is_active=True,
      is_deleted=False
    )

    app.dependency_overrides[get_current_user] = lambda: me_mock

    response = await client.get("/users/me")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Karl Marx"
    assert data["id"] == 123
    assert data["role"] == UserRole.USER
    assert data["is_active"] is True
    assert data["is_deleted"] is False

  async def test_get_me_unauthenticated(self, client: AsyncClient):
    app.dependency_overrides = {}

    response = await client.get("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated" # Default message

  async def test_get_me_inactive(self, client: AsyncClient):
    inactive_me = UserComplete(
      id=123,
      name="isaias",
      role=UserRole.USER,
      is_active=False,
      is_deleted=False
    )

    app.dependency_overrides[get_current_user] = lambda: inactive_me

    response = await client.get("/users/me")

    assert response.status_code == 400
    assert response.json()["detail"] == ErrorMessages.INACTIVE_USER

  async def test_get_me_deleted(self, client: AsyncClient):
    deleted_me = UserComplete(
      id=123,
      name="Karl Marx",
      role=UserRole.USER,
      is_active=False,
      is_deleted=True
    )

    app.dependency_overrides[get_current_user] = lambda: deleted_me

    response = await client.get("/users/me")

    assert response.status_code == 404
    assert response.json()["detail"] == ErrorMessages.USER_NOT_FOUND

class TestUpdateMe:
  async def test_update_user_success(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_db_user.id,
      name=fake_db_user.name,
      role=fake_db_user.role,
      is_active=fake_db_user.is_active,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name="newname")

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 200
    assert response.json()["name"] == "newname"

    user_res = await db_session.execute(select(User).where(User.name == "newname"))
    user_db = user_res.scalar_one_or_none()

    assert user_db is not None
    assert user_db.id == fake_db_user.id

  async def test_update_user_same_name(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_db_user.id,
      name=fake_db_user.name,
      role=fake_db_user.role,
      is_active=fake_db_user.is_active,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name=fake_db_user.name)

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 200
    # The same name, no errors
    assert response.json()["name"] == fake_db_user.name

    user_res = await db_session.execute(select(User).where(User.name == fake_db_user.name))
    user_db = user_res.scalar_one_or_none()

    assert user_db is not None
    assert user_db.id == fake_db_user.id

  async def test_update_me_unauthenticated(self, client: AsyncClient):
    app.dependency_overrides = {}

    response = await client.patch("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated" # Default message

  async def test_update_me_inactive(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=False, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_db_user.id,
      name=fake_db_user.name,
      role=fake_db_user.role,
      is_active=fake_db_user.is_active,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    response = await client.patch("/users/me")

    assert response.status_code == 400
    assert response.json()["detail"] == ErrorMessages.INACTIVE_USER

  async def test_update_me_deleted(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    db_session.add(fake_db_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_db_user.id,
      name=fake_db_user.name,
      role=fake_db_user.role,
      is_active=fake_db_user.is_active,
      is_deleted=fake_db_user.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    response = await client.patch("/users/me")

    assert response.status_code == 404
    assert response.json()["detail"] == ErrorMessages.USER_NOT_FOUND

  async def test_update_me_duplicate_name(self, client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    user2 = User(name="user2", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add_all([user1, user2])
    await db_session.flush()

    user_mock = UserComplete(
      id=user1.id,
      name="user1",
      role=UserRole.USER,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name=user2.name)

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 409
    assert response.json()["message"] == ErrorMessages.DUPLICATED_USERNAME

  async def test_update_me_empty_name(self, client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(user1)
    await db_session.flush()

    user_mock = UserComplete(
      id=user1.id,
      name=user1.name,
      role=user1.role,
      is_active=user1.is_active,
      is_deleted=user1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name="    ")

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.EMPTY_NAME

    await db_session.flush()

    user = await db_session.get(User, user1.id)

    assert user is not None
    assert user.name == "user1"

  async def test_update_me_white_space_short_name(self, client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(user1)
    await db_session.flush()

    user_mock = UserComplete(
      id=user1.id,
      name=user1.name,
      role=user1.role,
      is_active=user1.is_active,
      is_deleted=user1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name="    s")

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.SHORT_NAME

    await db_session.flush()

    user = await db_session.get(User, user1.id)

    assert user is not None
    assert user.name == "user1"

  async def test_update_me_white_space(self, client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(user1)
    await db_session.flush()

    user_mock = UserComplete(
      id=user1.id,
      name=user1.name,
      role=user1.role,
      is_active=user1.is_active,
      is_deleted=user1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    user_update = UserUpdate(name="  newname ")

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 200

    await db_session.flush()

    user = await db_session.get(User, user1.id)

    assert user is not None
    assert user.name == "newname"

  async def test_update_me_role_injection(self, client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(user1)
    await db_session.flush()

    user_mock = UserComplete(
      id=user1.id,
      name=user1.name,
      role=user1.role,
      is_active=user1.is_active,
      is_deleted=user1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    # IMPORTANT: This may fail for other reason if i update the UserUpdate scheme
    user_update = {
      "name": "newname",
      "role": UserRole.SUPERADMIN
    }

    response = await client.patch("/users/me", json=user_update)

    assert response.status_code == 200

    await db_session.flush()

    user = await db_session.get(User, user1.id)

    assert user is not None
    assert user.name == "newname"
    assert user.role == UserRole.USER

class TestsDeleteMe:
  async def test_delete_me_success(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(
      name="user",
      pw_hash="h",
      role=UserRole.USER,
      is_active=True,
      is_deleted=False
    )
    db_session.add(fake_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_user.id,
      name=fake_user.name,
      role=fake_user.role,
      is_active=fake_user.is_active,
      is_deleted=fake_user.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    assert res.status_code == 204

    await db_session.flush()

    assert fake_user.is_deleted is True # Then, the data is updated in the db (if there are no errors after)

  async def test_delete_me_admin(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(
      name="admin",
      pw_hash="h",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    db_session.add(fake_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_user.id,
      name=fake_user.name,
      role=fake_user.role,
      is_active=fake_user.is_active,
      is_deleted=fake_user.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    assert res.status_code == 204

    await db_session.flush()

    assert fake_user.is_deleted is True # Then, the data is updated in the db (if there are no errors after)

  async def test_delete_me_superadmin(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin1 = User(
      name="superadmin1",
      pw_hash="h",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    fake_superadmin2 = User(
      name="superadmin2",
      pw_hash="h",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    db_session.add_all([fake_superadmin1, fake_superadmin2])
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_superadmin1.id,
      name=fake_superadmin1.name,
      role=fake_superadmin1.role,
      is_active=fake_superadmin1.is_active,
      is_deleted=fake_superadmin1.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    assert res.status_code == 204

    await db_session.flush()

    assert fake_superadmin1.is_deleted is True # Then, the data is updated in the db (if there are no errors after)

  async def test_delete_me_last_superadmin(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin = User(
      name="superadmin",
      pw_hash="h",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    db_session.add(fake_superadmin)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_superadmin.id,
      name=fake_superadmin.name,
      role=fake_superadmin.role,
      is_active=fake_superadmin.is_active,
      is_deleted=fake_superadmin.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    assert res.status_code == 400
    assert res.json()["message"] == ErrorMessages.DELETE_LAST_SUPERADMIN

    await db_session.flush()

    superadmin = await db_session.get(User, fake_superadmin.id)

    assert superadmin is not None
    assert superadmin.name == "superadmin"
    assert superadmin.is_deleted is False

  async def test_delete_me_deleted(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(
      name="user",
      pw_hash="h",
      role=UserRole.USER,
      is_active=False,
      is_deleted=True
    )
    db_session.add(fake_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_user.id,
      name=fake_user.name,
      role=fake_user.role,
      is_active=fake_user.is_active,
      is_deleted=fake_user.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    assert res.status_code == 404
    assert res.json()["detail"] == ErrorMessages.USER_NOT_FOUND
    assert fake_user.is_deleted is True

  async def test_delete_me_inactive(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(
      name="user",
      pw_hash="h",
      role=UserRole.USER,
      is_active=False,
      is_deleted=False
    )
    db_session.add(fake_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_user.id,
      name=fake_user.name,
      role=fake_user.role,
      is_active=fake_user.is_active,
      is_deleted=fake_user.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    res = await client.delete("/users/me")

    await db_session.flush()

    assert res.status_code == 400
    assert res.json()["detail"] == ErrorMessages.INACTIVE_USER
    assert fake_user.is_deleted is False

  # IMPORTANT TEST: implement a tests that first deletes an user successfully and then,
  # that user tries to access GET /users/me, this should return 404 NOT FOUND
  # for this tests i need to use real JWT tokens

  async def test_delete_me_name_liberation(self, client: AsyncClient, db_session: AsyncSession):
    name = "user"

    fake_user = User(
      name=name,
      pw_hash="h",
      role=UserRole.USER,
      is_active=True,
      is_deleted=False
    )
    db_session.add(fake_user)
    await db_session.flush()

    user_mock = UserComplete(
      id=fake_user.id,
      name=fake_user.name,
      role=fake_user.role,
      is_active=fake_user.is_active,
      is_deleted=fake_user.is_deleted
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    new_user_scheme = UserCreate(
      name=name,
      password="password123",
      password_confirm="password123"
    )

    res = await client.post("/users/", json=new_user_scheme.model_dump())
    assert res.status_code == 409

    res = await client.delete("/users/me")
    assert res.status_code == 204

    await db_session.flush()

    assert fake_user.is_deleted is True

    res = await client.post("/users/", json=new_user_scheme.model_dump())
    assert res.status_code == 201
