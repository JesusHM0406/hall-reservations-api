from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.messages import ErrorMessages
from app.main import app
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserComplete, UserUpdate

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

    user_update = UserUpdate(name="user2")

    response = await client.patch("/users/me", json=user_update.model_dump())

    assert response.status_code == 409
    assert response.json()["message"] == ErrorMessages.DUPLICATED_USERNAME

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

    assert fake_user.is_deleted is True # Then, the data is updated in the db (if there are no errors after)

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

    assert res.status_code == 400
    assert res.json()["detail"] == ErrorMessages.INACTIVE_USER
    assert fake_user.is_deleted is False
