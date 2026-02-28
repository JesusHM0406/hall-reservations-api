from typing import Any

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate


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
      name="Karl Marx",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Karl Marx"

    assert "pw_hash" not in data
    assert "password" not in data

    new_user = await db_session.get(User, data["id"])

    assert new_user is not None
    assert new_user.role == UserRole.USER

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

  # Added again just to be sure I haven't forgotten the validation
  async def test_create_user_passwords_mismatch(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    # IMPORTANT: This may fail for other reason if i update the UserCreate scheme
    user_schema: dict[str, Any] = {
      "name":"Karl Marx",
      "password":"password",
      "password_confirm":"otherpassword"
    }

    response = await client.post("/users/", json=user_schema)

    assert response.status_code == 422

    data = response.json()
    assert ErrorMessages.PASSWORDS_MISMATCH in data["detail"][0]["msg"] # Pydantic errors structure

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

  async def test_create_user_white_space_short_name(
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
      name="     s",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 400

    data = response.json()
    assert data["message"] == ErrorMessages.SHORT_NAME

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

  async def test_create_user_role_injection(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    # IMPORTANT: This may fail for other reason if i update the UserCreate scheme
    user_schema: dict[str, Any] = {
      "name":"Karl Marx",
      "password":"password",
      "password_confirm":"password",
      "role":UserRole.SUPERADMIN
    }

    response = await client.post("/users/", json=user_schema)

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Karl Marx"

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count + 1

    db_user = await db_session.get(User, data["id"])

    assert db_user is not None
    assert db_user.role == UserRole.USER


class TestRegistrationRateLimiting:
  """Test rate limiting functionality on registration endpoint."""

  async def test_rate_limit_allows_initial_attempts(
    self,
    client: AsyncClient
  ):
    """Test that initial registration attempts are allowed."""
    # First 3 attempts should be allowed (max_attempts=3 for registration)
    for i in range(3):
      user_schema = UserCreate(
        name=f"testuser{i}",
        password="password123",
        password_confirm="password123"
      )
      response = await client.post("/users/", json=user_schema.model_dump())
      # Should return 201 (created), not 429 (rate limit)
      assert response.status_code == 201

  async def test_rate_limit_blocks_after_max_attempts(
    self,
    client: AsyncClient
  ):
    """Test that rate limit blocks after exceeding max attempts."""
    # Make 3 registration attempts (max_attempts)
    for i in range(3):
      user_schema = UserCreate(
        name=f"testuser{i}",
        password="password123",
        password_confirm="password123"
      )
      response = await client.post("/users/", json=user_schema.model_dump())
      assert response.status_code == 201

    # 4th attempt should be rate limited
    user_schema = UserCreate(
      name="testuser_blocked",
      password="password123",
      password_confirm="password123"
    )
    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 429
    assert "Too many registration attempts" in response.json()["detail"]

  async def test_rate_limit_returns_retry_after_header(
    self,
    client: AsyncClient
  ):
    """Test that rate limit response includes Retry-After header."""
    # Exceed rate limit
    for i in range(3):
      user_schema = UserCreate(
        name=f"testuser{i}",
        password="password123",
        password_confirm="password123"
      )
      await client.post("/users/", json=user_schema.model_dump())

    # Rate limited request should have Retry-After header
    user_schema = UserCreate(
      name="testuser_blocked",
      password="password123",
      password_confirm="password123"
    )
    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 429
    assert "retry-after" in response.headers
    # Retry-after should be a positive integer (seconds)
    retry_after = int(response.headers["retry-after"])
    assert retry_after > 0

  async def test_rate_limit_counts_failed_attempts(
    self,
    client: AsyncClient
  ):
    """Test that rate limit counts both successful and failed registration attempts."""
    # 2 successful registrations
    for i in range(2):
      user_schema = UserCreate(
        name=f"testuser{i}",
        password="password123",
        password_confirm="password123"
      )
      response = await client.post("/users/", json=user_schema.model_dump())
      assert response.status_code == 201

    # 1 failed attempt (duplicate name)
    user_schema = UserCreate(
      name="testuser0",  # Duplicate
      password="password123",
      password_confirm="password123"
    )
    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 409  # Conflict

    # 4th attempt should be rate limited (3 max attempts reached)
    user_schema = UserCreate(
      name="testuser_blocked",
      password="password123",
      password_confirm="password123"
    )
    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 429
    assert "Too many registration attempts" in response.json()["detail"]
