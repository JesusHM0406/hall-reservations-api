from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.messages import ErrorMessages
from app.main import app
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.filters.user import UserFilterNames, UserRoleFilter, UserStatusFilter
from app.schemas.user import UserComplete, UserCreate


class TestCreateUser:
  async def test_create_user_success(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="name",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "name"

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count + 1

  async def test_create_user_duplicated(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    fake_user = User(
      name="name",
      pw_hash="fakepasswordhash"
    )

    db_session.add(fake_user)
    await db_session.flush()

    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    assert before_total_count > 0

    new_user_schema = UserCreate(
      name="name",
      password="newpassword",
      password_confirm="newpassword"
    )

    response = await client.post("/users/", json=new_user_schema.model_dump())

    assert response.status_code == 409

    data = response.json()
    assert data["message"] == ErrorMessages.DUPLICATED_USERNAME

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_password_mismatch(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="name",
      password="password",
      password_confirm="otherpassword"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 400

    data = response.json()
    assert data["message"] == ErrorMessages.PASSWORDS_MISMATCH

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_white_space_name(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="     ",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 400

    data = response.json()
    assert data["message"] == ErrorMessages.EMPTY_NAME

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_white_space_name_success(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="  name   ",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "name"

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count + 1


class TestGetUsers:
  async def test_get_users_empty_admin(self, client: AsyncClient):
    # Simulates an admin in the db
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True
    )

    app.dependency_overrides[get_current_user] = lambda: admin_mock

    response = await client.get("/users/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0

  async def test_get_users_user(self, client: AsyncClient):
    # Simulates an user in the db
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.USER,
      is_active=True
    )

    app.dependency_overrides[get_current_user] = lambda: user_mock

    response = await client.get("/users/")

    assert response.status_code == 403

    data = response.json()
    assert data["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_get_users_unauthenticated(self, client: AsyncClient):
    response = await client.get("/users/")

    assert response.status_code == 401

    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_get_users_inactive_admin(self, client: AsyncClient):
    # Simulates an admin in the db
    admin_mock = UserComplete(
      id=1,
      name="admin",
      role=UserRole.ADMIN,
      is_active=False
    )

    app.dependency_overrides[get_current_user] = lambda: admin_mock

    response = await client.get("/users/")

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == ErrorMessages.INACTIVE_USER

  async def test_get_users_with_data(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user1 = User(name="juan", pw_hash="hash1")
    user2 = User(name="maria", pw_hash="hash2")
    db_session.add_all([user1, user2])
    await db_session.flush()

    response = await client.get("/users/")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 2

    names = [u["name"] for u in data["items"]]
    assert "juan" in names
    assert "maria" in names

    for user in data["items"]:
      assert "pw_hash" not in user
      assert "password" not in user

  async def test_get_users_pagination_logic(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(id=999, name="admin", role=UserRole.ADMIN, is_active=True)
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    users = [User(name=f"user_{i}", pw_hash="hash") for i in range(15)]
    db_session.add_all(users)
    await db_session.flush()

    response = await client.get("/users/?page=1")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 15
    assert len(data["items"]) == settings.PAGINATION_LIMIT_PER_PAGE
    assert data["pages"] == 2
    assert data["current_page"] == 1
    assert data["has_next"] is True
    assert data["has_prev"] is False
    assert data["next_num"] == 2

    response = await client.get("/users/?page=2")
    data = response.json()

    assert len(data["items"]) == 5
    assert data["current_page"] == 2
    assert data["has_next"] is False
    assert data["has_prev"] is True
    assert data["prev_num"] == 1

  async def test_get_users_pagination_boundaries(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(id=999, name="admin", role=UserRole.ADMIN, is_active=True)
    app.dependency_overrides[get_current_user] = lambda: admin_mock
    users = [User(name=f"u{i}", pw_hash="h") for i in range(15)]
    db_session.add_all(users)
    await db_session.flush()

    # If the requested page is less than 1, the current page should be 1,
    # the first page, and this is the page that should be used in the query
    res_min = await client.get("/users/?page=0")
    data = res_min.json()
    assert data["requested_page"] == 0
    assert data["current_page"] == 1
    # because the current_page should be the page used in the query this need
    # to show all the results from the first page, and not to be empty
    assert len(data["items"]) == settings.PAGINATION_LIMIT_PER_PAGE

    # If the requested page is greater than the max page, the current page should
    #  be the last page, in this case, the last page is 2 because the limit is of 10
    # and there are 15 users in the database (the fake one)
    res_max = await client.get("/users/?page=100")
    data = res_max.json()

    assert data["requested_page"] == 100
    assert data["current_page"] == 2
    assert len(data["items"]) == 5

  async def test_get_users_filters(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(id=999, name="admin", role=UserRole.ADMIN, is_active=True)
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    # 1 active admin, 2 active users, 1 inactive user
    u1 = User(name="admin_active", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u2 = User(name="user_active_1", role=UserRole.USER, is_active=True, pw_hash="h")
    u3 = User(name="user_active_2", role=UserRole.USER, is_active=True, pw_hash="h")
    u4 = User(name="user_inactive", role=UserRole.USER, is_active=False, pw_hash="h")

    db_session.add_all([u1, u2, u3, u4])
    await db_session.flush()

    # Only admins
    res = await client.get(f"/users/?{UserFilterNames.ROLE.value}={UserRoleFilter.ADMIN.value}")
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "admin_active"

    # Only inactive ones
    res = await client.get(f"/users/?{UserFilterNames.STATUS.value}={UserStatusFilter.INACTIVE.value}")
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "user_inactive"

    # Only users and active ones (mixed)
    res = await client.get(f"/users/?{UserFilterNames.ROLE.value}={UserRoleFilter.USER.value}&{UserFilterNames.STATUS.value}={UserStatusFilter.ACTIVE.value}")
    assert res.json()["total"] == 2
