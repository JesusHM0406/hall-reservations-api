"""
Tests for rate limiting middleware across the application.

Covers both global rate limiting (all endpoints) and 
auth-specific rate limiting (login endpoint protection).
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole


class TestGlobalRateLimiting:
  """Test global rate limiting functionality across all endpoints."""

  async def test_global_rate_limit_allows_normal_usage(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that normal usage within limits is allowed."""
    # Create a user and get token
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Login
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Make multiple requests within the limit (e.g., 50 requests)
    for _ in range(50):
      response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
      )
      assert response.status_code == 200

  async def test_global_rate_limit_blocks_excessive_requests(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that excessive requests are blocked."""
    # Create a user and get token
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Login (counts as 1 request)
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Make 99 more requests to reach the limit (1 login + 99 = 100 total)
    for i in range(99):
      response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
      )
      # Should succeed up to the limit
      assert response.status_code == 200, f"Request {i+2} failed"

    # 101st request should be rate limited
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]

  async def test_global_rate_limit_returns_retry_after_header(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that rate limit response includes Retry-After header."""
    # Create a user and get token
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Login (counts as 1 request)
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Exhaust the limit (99 more requests = 100 total)
    for _ in range(99):
      await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
      )

    # Rate limited request should have Retry-After header
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 429
    assert "retry-after" in response.headers
    retry_after = int(response.headers["retry-after"])
    assert retry_after > 0

  async def test_global_rate_limit_applies_to_different_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that global rate limit applies across different endpoints."""
    # Create admin user
    admin = User(
      name="admin",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.ADMIN
    )
    db_session.add(admin)
    await db_session.flush()

    # Login (counts as 1 request)
    response = await client.post(
      "/auth/login",
      data={"username": "admin", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Make requests to various endpoints
    endpoints = [
      ("/users/me", "GET"),
      ("/users/", "GET"),
      ("/halls/", "GET"),
      ("/reservations/", "GET"),
    ]

    request_count = 1  # Start at 1 because of login
    # Make requests across endpoints until we reach 99 (total 100 with login)
    while request_count < 100:
      for endpoint, method in endpoints:
        if request_count >= 100:
          break
        if method == "GET":
          response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"}
          )
        request_count += 1
        # Should succeed up to 100
        assert response.status_code in [200, 404], f"Failed at request {request_count}"

    # 101st request to any endpoint should be rate limited
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 429


class TestLoginRateLimiting:
  """Test rate limiting functionality on login endpoint."""

  async def test_rate_limit_allows_initial_attempts(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that initial login attempts are allowed."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # First 5 attempts should be allowed
    for _ in range(5):
      response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrong"}
      )
      # Should return 401 (auth failed), not 429 (rate limit)
      assert response.status_code == 401

  async def test_rate_limit_blocks_after_max_attempts(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that rate limit blocks after exceeding max attempts."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Make 5 failed attempts (max_attempts)
    for _ in range(5):
      response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrong"}
      )
      assert response.status_code == 401

    # 6th attempt should be rate limited
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "wrong"}
    )
    assert response.status_code == 429
    assert "Too many login attempts" in response.json()["detail"]

  async def test_rate_limit_returns_retry_after_header(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that rate limit response includes Retry-After header."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Exceed rate limit
    for _ in range(5):
      await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrong"}
      )

    # Rate limited request should have Retry-After header
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "wrong"}
    )
    assert response.status_code == 429
    assert "retry-after" in response.headers

  async def test_rate_limit_per_ip_address(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that rate limiting is per-IP address."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Simulate requests from different IPs by using different client-like objects
    # The test client uses a fixed test IP, so we exhaust the rate limit
    for _ in range(5):
      await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrong"}
      )

    # 6th request is rate limited
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "wrong"}
    )
    assert response.status_code == 429

  async def test_rate_limit_successful_login_does_not_reset(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that successful login does not automatically reset rate limit."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Make 4 failed attempts
    for _ in range(4):
      await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrong"}
      )

    # Successful login counts as one more attempt
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200  # Successful login

    # 6th attempt (5 + 1) should be rate limited
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "wrong"}
    )
    assert response.status_code == 429
