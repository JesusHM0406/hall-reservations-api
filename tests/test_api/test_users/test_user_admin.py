from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.messages import ErrorMessages
from app.main import app
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.filters.user import UserFilterNames, UserRoleFilter, UserStatusFilter
from app.schemas.user import UserAdminUpdate, UserComplete

class TestGetUsers:
  async def test_get_users_empty_admin(self, client: AsyncClient):
    # Simulates an admin in the db
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
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
      is_active=True,
      is_deleted=False
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
      is_active=False,
      is_deleted=False
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
      is_active=True,
      is_deleted=False
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
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
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
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
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
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
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

  async def test_get_users_deleted(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    # 1 active admin, 2 active users, 3 deleted users
    u1 = User(name="admin_active", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u2 = User(name="user_active_1", role=UserRole.USER, is_active=True, pw_hash="h")
    u3 = User(name="user_active_2", role=UserRole.USER, is_active=True, pw_hash="h")
    u4 = User(name="user_deleted1", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u5 = User(name="user_deleted2", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u6 = User(name="user_deleted3", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)

    db_session.add_all([u1, u2, u3, u4, u5, u6])
    await db_session.flush()

    # Only deleted ones
    res = await client.get(f"/users/?{UserFilterNames.STATUS.value}={UserStatusFilter.DELETED.value}")
    data = res.json()
    items = data["items"]

    assert data["total"] == 3
    assert len(items) == 3

    for i in range(len(items)):
      assert items[i]["is_deleted"] is True

  async def test_admin_cannot_see_superadmins(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    # 3 active admins, 2 active users, 2 deleted users, 2 superadmins
    u1 = User(name="admin_active", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u2 = User(name="user_active_1", role=UserRole.USER, is_active=True, pw_hash="h")
    u3 = User(name="user_active_2", role=UserRole.USER, is_active=True, pw_hash="h")
    u4 = User(name="user_deleted1", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u5 = User(name="user_deleted2", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u6 = User(name="admin_active2", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u7 = User(name="admin_active3", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u8 = User(name="superadmin_active1", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    u9 = User(name="superadmin_active2", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")


    db_session.add_all([u1, u2, u3, u4, u5, u6, u7, u8, u9])
    await db_session.flush()

    # All users except superadmins
    res = await client.get("/users/")
    data = res.json()
    assert data["total"] == 7

    filters = data["available_filters"]
    role_filter = filters[0]
    assert role_filter["name"] == UserFilterNames.ROLE
    role_option_values = [o["value"] for o in role_filter["options"]]
    assert UserRoleFilter.SUPERADMIN.value not in role_option_values
    assert UserRoleFilter.ADMIN.value in role_option_values
    assert UserRoleFilter.USER.value in role_option_values

    items = data["items"]
    assert len(items) == 7
    roles = [item["role"] for item in items]
    assert UserRole.SUPERADMIN not in roles

    # Superadmin filter forced (ignored)
    res = await client.get(f"/users/?{UserFilterNames.ROLE.value}={UserRoleFilter.SUPERADMIN.value}")
    data = res.json()
    assert data["total"] == 7

    items = data["items"]
    assert len(items) == 7
    roles = [item["role"] for item in items]
    assert UserRole.SUPERADMIN not in roles

  async def test_get_all_users_superadmin(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="superadmin",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    # 3 active admins, 2 active users, 2 deleted users, 2 superadmins
    u1 = User(name="admin_active", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u2 = User(name="user_active_1", role=UserRole.USER, is_active=True, pw_hash="h")
    u3 = User(name="user_active_2", role=UserRole.USER, is_active=True, pw_hash="h")
    u4 = User(name="user_deleted1", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u5 = User(name="user_deleted2", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    u6 = User(name="admin_active2", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u7 = User(name="admin_active3", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    u8 = User(name="superadmin_active1", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    u9 = User(name="superadmin_active2", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")

    db_session.add_all([u1, u2, u3, u4, u5, u6, u7, u8, u9])
    await db_session.flush()

    # All users including superadmins
    res = await client.get("/users/")
    data = res.json()
    assert data["total"] == 9

    items = data["items"]
    roles = [item["role"] for item in items]
    assert UserRole.SUPERADMIN in roles

    filters = data["available_filters"]
    role_filter = filters[0]
    assert role_filter["name"] == UserFilterNames.ROLE
    role_option_values = [o["value"] for o in role_filter["options"]]
    assert UserRoleFilter.SUPERADMIN.value in role_option_values
    assert UserRoleFilter.ADMIN.value in role_option_values
    assert UserRoleFilter.USER.value in role_option_values

    # Superadmin filter (accepted)
    res = await client.get(f"/users/?{UserFilterNames.ROLE.value}={UserRoleFilter.SUPERADMIN.value}")
    data = res.json()
    assert data["total"] == 2

    items = data["items"]
    assert len(items) == 2

    roles = [item["role"] for item in items]
    assert UserRole.SUPERADMIN in roles
    assert UserRole.ADMIN not in roles
    assert UserRole.USER not in roles

class TestGetUserByID:
  async def test_get_user_by_id_success(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    fake_user = User(name="fake", pw_hash="h")
    other_user = User(name="other", pw_hash="h")

    db_session.add_all([fake_user, other_user])
    await db_session.flush()

    res = await client.get(f"/users/{fake_user.id}")

    assert res.status_code == 200

    data = res.json()

    assert data["name"] == "fake"
    assert data["role"] == UserRole.USER

  async def test_get_user_by_id_not_found(self, client: AsyncClient):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    # It is assumed that ID 9999 does not exist
    response = await client.get("/users/9999")

    assert response.status_code == 404
    assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

  async def test_get_user_by_id_as_regular_user(self, client: AsyncClient):
    # User without admin role
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.USER,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    response = await client.get("/users/2")

    assert response.status_code == 403
    assert response.json()["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_get_admin_as_admin(self, client: AsyncClient, db_session: AsyncSession):
    # Admin role
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    fake_user = User(name="fake", pw_hash="h")
    other_user = User(name="other", pw_hash="h")

    db_session.add_all([fake_user, other_user])
    await db_session.flush()

    response = await client.get(f"/users/{fake_user.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == fake_user.id
    assert data["name"] == fake_user.name
    assert data["role"] == fake_user.role.value
    assert data["is_active"] == fake_user.is_active
    assert data["is_deleted"] == fake_user.is_deleted

  async def test_get_superadmin_as_admin(self, client: AsyncClient, db_session: AsyncSession):
    # Admin role
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    fake_superadmin = User(name="fake", pw_hash="h", role=UserRole.SUPERADMIN)

    db_session.add(fake_superadmin)
    await db_session.flush()

    response = await client.get(f"/users/{fake_superadmin.id}")

    assert response.status_code == 404
    assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

  async def test_get_superadmin_as_superadmin(self, client: AsyncClient, db_session: AsyncSession):
    # Superadmin role
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    fake_superadmin = User(name="fake", pw_hash="h", role=UserRole.SUPERADMIN)

    db_session.add(fake_superadmin)
    await db_session.flush()

    response = await client.get(f"/users/{fake_superadmin.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == fake_superadmin.id
    assert data["name"] == fake_superadmin.name
    assert data["role"] == fake_superadmin.role.value
    assert data["is_active"] == fake_superadmin.is_active
    assert data["is_deleted"] == fake_superadmin.is_deleted

  async def test_get_admin_as_superadmin(self, client: AsyncClient, db_session: AsyncSession):
    # Superadmin role
    user_mock = UserComplete(
      id=1,
      name="user",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: user_mock

    fake_admin = User(name="fake", pw_hash="h", role=UserRole.ADMIN)

    db_session.add(fake_admin)
    await db_session.flush()

    response = await client.get(f"/users/{fake_admin.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == fake_admin.id
    assert data["name"] == fake_admin.name
    assert data["role"] == fake_admin.role.value
    assert data["is_active"] == fake_admin.is_active
    assert data["is_deleted"] == fake_admin.is_deleted

  async def test_get_user_by_id_deleted(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    fake_user = User(name="fake", pw_hash="h", is_active=False, is_deleted=True)

    db_session.add(fake_user)
    await db_session.flush()

    res = await client.get(f"/users/{fake_user.id}")

    assert res.status_code == 404
    assert res.json()["message"] == ErrorMessages.USER_NOT_FOUND

  async def test_get_user_by_id_inactive(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    fake_user = User(name="fake", pw_hash="h", is_active=False, is_deleted=False)

    db_session.add(fake_user)
    await db_session.flush()

    res = await client.get(f"/users/{fake_user.id}")

    assert res.status_code == 200

  async def test_get_user_by_id_not_int(self, client: AsyncClient, db_session: AsyncSession):
    admin_mock = UserComplete(
      id=999,
      name="admin",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    res = await client.get("/users/string")

    # FastAPI Validation
    assert res.status_code == 422

class TestUpdateById:
  async def test_admin_updates_normal_user_success(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="newname",
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 200
    assert response.json()["name"] == "newname"

    user_res = await db_session.execute(select(User).where(User.name == "newname"))
    user_db = user_res.scalar_one_or_none()

    assert user_db is not None
    assert user_db.id == fake_db_user.id

  async def test_admin_updates_normal_user_no_info(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "user"
    assert data["role"] == UserRole.USER
    assert data["is_active"] is True
    assert data["is_deleted"] is False

    user_db = await db_session.get(User, fake_db_user.id)

    assert user_db is not None
    assert user_db.name == "user"
    assert user_db.role == UserRole.USER
    assert user_db.is_active is True
    assert user_db.is_deleted is False

  async def test_admin_updates_normal_user_same_name(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=fake_db_user.name,
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "user"
    assert data["role"] == UserRole.USER
    assert data["is_active"] is True
    assert data["is_deleted"] is False

    user_db = await db_session.get(User, fake_db_user.id)

    assert user_db is not None
    assert user_db.name == "user"
    assert user_db.role == UserRole.USER
    assert user_db.is_active is True
    assert user_db.is_deleted is False

  async def test_superadmin_promotes_user_to_admin(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    # Just to be sure, humans often make many mistakes without realizing it.
    assert fake_db_user.role == UserRole.USER

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="newname",
      role=UserRole.ADMIN,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "newname"
    assert data["role"] == UserRole.ADMIN

    user_res = await db_session.execute(select(User).where(User.name == "newname"))
    user_db = user_res.scalar_one_or_none()

    assert user_db is not None
    assert user_db.id == fake_db_user.id
    assert user_db.role == UserRole.ADMIN

  async def test_superadmin_downgrades_admin_to_user(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    # Just to be sure, humans often make many mistakes without realizing it.
    assert fake_db_user.role == UserRole.ADMIN

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.SUPERADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=UserRole.USER,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "user"
    assert data["role"] == UserRole.USER

    user_db = await db_session.get(User, fake_db_user.id)

    assert user_db is not None
    assert user_db.id == fake_db_user.id
    assert user_db.role == UserRole.USER

  async def test_superadmin_self_demotes_success(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin1 = User(name="superadmin1", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    fake_superadmin2 = User(name="superadmin2", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    db_session.add_all([fake_superadmin1, fake_superadmin2])
    await db_session.flush()

    admin_mock = UserComplete(
      id=fake_superadmin2.id,
      name=fake_superadmin2.name,
      role=fake_superadmin2.role,
      is_active=fake_superadmin2.is_active,
      is_deleted=fake_superadmin2.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=UserRole.USER,
      is_active=None
    )

    response = await client.patch(f"/users/{admin_mock.id}", json=user_update.model_dump())

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == fake_superadmin2.name
    assert data["role"] == UserRole.USER

    user_db = await db_session.get(User, admin_mock.id)

    assert user_db is not None
    assert user_db.role == UserRole.USER

  async def test_admin_promotes_user_to_admin_fail(self, client: AsyncClient, db_session: AsyncSession):
    fake_db_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_db_user)
    await db_session.flush()

    # Just to be sure, humans often make many mistakes without realizing it.
    assert fake_db_user.role == UserRole.USER

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="newname",
      role=UserRole.ADMIN,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_db_user.id}", json=user_update.model_dump())

    assert response.status_code == 403
    assert response.json()["message"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS_UPDATE_ROLE

    await db_session.flush()

    user_db = await db_session.get(User, fake_db_user.id)

    assert user_db is not None
    assert user_db.role == UserRole.USER
    assert user_db.name == "user"

  async def test_admin_updates_superadmin_fail(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin = User(name="superadmin", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    db_session.add(fake_superadmin)
    await db_session.flush()

    # Just to be sure, humans often make many mistakes without realizing it.
    assert fake_superadmin.role == UserRole.SUPERADMIN

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="newname",
      role=UserRole.ADMIN,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_superadmin.id}", json=user_update.model_dump())

    assert response.status_code == 404
    assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

    await db_session.flush()

    superadmin_db = await db_session.get(User, fake_superadmin.id)

    assert superadmin_db is not None
    assert superadmin_db.role == UserRole.SUPERADMIN
    assert superadmin_db.name == "superadmin"

  async def test_admin_self_promotes(self, client: AsyncClient, db_session: AsyncSession):
    fake_admin = User(name="admin", role=UserRole.ADMIN, is_active=True, pw_hash="h")
    db_session.add(fake_admin)
    await db_session.flush()

    # Just to be sure, humans often make many mistakes without realizing it.
    assert fake_admin.role == UserRole.ADMIN

    admin_mock = UserComplete(
      id=fake_admin.id,
      name=fake_admin.name,
      role=fake_admin.role,
      is_active=fake_admin.is_active,
      is_deleted=fake_admin.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=UserRole.SUPERADMIN,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_admin.id}", json=user_update.model_dump())

    assert response.status_code == 400
    data = response.json()
    assert data["message"] == ErrorMessages.CANNOT_UPDATE

    await db_session.flush()

    admin_db = await db_session.get(User, fake_admin.id)

    assert admin_db is not None
    assert admin_db.role == UserRole.ADMIN

  async def test_last_superadmin_self_demotes_fail(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin1 = User(name="superadmin1", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    db_session.add(fake_superadmin1)
    await db_session.flush()

    admin_mock = UserComplete(
      id=fake_superadmin1.id,
      name=fake_superadmin1.name,
      role=fake_superadmin1.role,
      is_active=fake_superadmin1.is_active,
      is_deleted=fake_superadmin1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=UserRole.USER,
      is_active=None
    )

    response = await client.patch(f"/users/{admin_mock.id}", json=user_update.model_dump())

    assert response.status_code == 400
    data = response.json()
    assert data["message"] == ErrorMessages.CANNOT_DOWNGRADE_LAST_SUPERADMIN

    superadmin_db = await db_session.get(User, fake_superadmin1.id)

    assert superadmin_db is not None
    assert superadmin_db.role == UserRole.SUPERADMIN

  async def test_last_superadmin_self_disables_fail(self, client: AsyncClient, db_session: AsyncSession):
    fake_superadmin1 = User(name="superadmin1", role=UserRole.SUPERADMIN, is_active=True, pw_hash="h")
    db_session.add(fake_superadmin1)
    await db_session.flush()

    admin_mock = UserComplete(
      id=fake_superadmin1.id,
      name=fake_superadmin1.name,
      role=fake_superadmin1.role,
      is_active=fake_superadmin1.is_active,
      is_deleted=fake_superadmin1.is_deleted
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name=None,
      role=None,
      is_active=False
    )

    response = await client.patch(f"/users/{admin_mock.id}", json=user_update.model_dump())

    assert response.status_code == 400
    data = response.json()
    assert data["message"] == ErrorMessages.DISABLE_LAST_SUPERADMIN

    superadmin_db = await db_session.get(User, fake_superadmin1.id)

    assert superadmin_db is not None
    assert superadmin_db.role == UserRole.SUPERADMIN

  async def test_admin_updates_normal_user_duplicated_name(self, client: AsyncClient, db_session: AsyncSession):
    fake_user1 = User(name="user1", role=UserRole.USER, is_active=True, pw_hash="h")
    fake_user2 = User(name="user2", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add_all([fake_user1, fake_user2])
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="user2",
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_user1.id}", json=user_update.model_dump())

    assert response.status_code == 409
    assert response.json()["message"] == ErrorMessages.DUPLICATED_USERNAME

    user1_db = await db_session.get(User, fake_user1.id)

    assert user1_db is not None
    assert user1_db.name == "user1"

  async def test_admin_updates_deleted_user(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(name="user", role=UserRole.USER, is_active=False, pw_hash="h", is_deleted=True)
    db_session.add(fake_user)
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="newname",
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_user.id}", json=user_update.model_dump())

    assert response.status_code == 404
    assert response.json()["message"] == ErrorMessages.USER_NOT_FOUND

    user_db = await db_session.get(User, fake_user.id)

    assert user_db is not None
    assert user_db.name == "user"

  async def test_admin_updates_empty_name(self, client: AsyncClient, db_session: AsyncSession):
    fake_user = User(name="user", role=UserRole.USER, is_active=True, pw_hash="h")
    db_session.add(fake_user)
    await db_session.flush()

    admin_mock = UserComplete(
      id=888,
      name="the one",
      role=UserRole.ADMIN,
      is_active=True,
      is_deleted=False
    )
    app.dependency_overrides[get_current_user] = lambda: admin_mock

    user_update = UserAdminUpdate(
      name="    ",
      role=None,
      is_active=None
    )

    response = await client.patch(f"/users/{fake_user.id}", json=user_update.model_dump())

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.EMPTY_NAME

    user_db = await db_session.get(User, fake_user.id)

    assert user_db is not None
    assert user_db.name == "user"
