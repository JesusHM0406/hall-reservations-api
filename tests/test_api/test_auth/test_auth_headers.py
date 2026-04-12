"""
Tests for security-related HTTP headers.

Verifies that proper security headers are included
in authentication error responses.
"""
from httpx import AsyncClient


class TestSecurityHeaders:
  """Test security-related HTTP headers and responses."""

  async def test_unauthorized_includes_www_authenticate(
    self,
    client: AsyncClient
  ):
    """Test that 401 responses include WWW-Authenticate header."""
    response = await client.get("/users/me")

    assert response.status_code == 401
    # FastAPI OAuth2PasswordBearer should add this header
    assert "www-authenticate" in response.headers

  async def test_invalid_token_includes_www_authenticate(
    self,
    client: AsyncClient
  ):
    """Test that invalid token returns WWW-Authenticate header."""
    response = await client.get(
      "/users/me",
      headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
    assert "www-authenticate" in response.headers
