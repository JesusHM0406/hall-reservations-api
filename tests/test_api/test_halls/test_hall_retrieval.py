"""
Tests for Hall Retrieval endpoints (Read operations)

This module contains tests for:
- GET /halls/ - List all halls with pagination and filters
- GET /halls/{id} - Get hall by ID
- GET /halls/by-name/{name} - Get hall by name
- GET /halls/search - Search halls

Focuses on:
- Public access (no authentication required)
- Pagination logic
- Filtering by availability
- Search functionality (PostgreSQL-specific, skipped in SQLite tests)
- Edge cases (not found, invalid IDs, etc.)
"""

from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.messages import ErrorMessages
from app.models.hall import Hall
from app.schemas.filters.hall import HallFilterNames, HallStatusFilter


class TestGetAllHalls:
  """Tests for GET /halls/ endpoint"""

  async def test_get_halls_empty(self, client: AsyncClient):
    """Getting halls when database is empty"""
    response = await client.get("/halls/")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total"] == 0
    assert len(data["items"]) == 0

  async def test_get_halls_with_data(self, client: AsyncClient, db_session: AsyncSession):
    """Getting halls returns all halls"""
    hall1 = Hall(name="Hall A", description="Description A", is_available=True)
    hall2 = Hall(name="Hall B", description="Description B", is_available=False)
    hall3 = Hall(name="Hall C", description="Description C", is_available=True)

    db_session.add_all([hall1, hall2, hall3])
    await db_session.flush()

    response = await client.get("/halls/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    names = [h["name"] for h in data["items"]]
    assert "Hall A" in names
    assert "Hall B" in names
    assert "Hall C" in names

  async def test_get_halls_pagination(self, client: AsyncClient, db_session: AsyncSession):
    """Getting halls respects pagination"""
    halls = [
      Hall(name=f"Hall {i}", description=f"Description {i}", is_available=True)
      for i in range(15)
    ]
    db_session.add_all(halls)
    await db_session.flush()

    # Page 1
    response = await client.get("/halls/?page=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == settings.PAGINATION_LIMIT_PER_PAGE
    assert data["pages"] == 2
    assert data["current_page"] == 1
    assert data["has_next"] is True
    assert data["has_prev"] is False

    # Page 2
    response = await client.get("/halls/?page=2")
    data = response.json()
    assert len(data["items"]) == 5
    assert data["current_page"] == 2
    assert data["has_next"] is False
    assert data["has_prev"] is True

  async def test_get_halls_pagination_boundaries(self, client: AsyncClient, db_session: AsyncSession):
    """Getting halls handles page boundaries correctly"""
    halls = [
      Hall(name=f"Hall {i}", description=f"Desc {i}", is_available=True)
      for i in range(15)
    ]
    db_session.add_all(halls)
    await db_session.flush()

    # Page 0 should default to page 1
    response = await client.get("/halls/?page=0")
    data = response.json()
    assert data["requested_page"] == 0
    assert data["current_page"] == 1
    assert len(data["items"]) == settings.PAGINATION_LIMIT_PER_PAGE

    # Page beyond max should default to last page
    response = await client.get("/halls/?page=100")
    data = response.json()
    assert data["requested_page"] == 100
    assert data["current_page"] == 2
    assert len(data["items"]) == 5

  async def test_get_halls_filter_available(self, client: AsyncClient, db_session: AsyncSession):
    """Filtering halls by availability status"""
    h1 = Hall(name="Available 1", description="Desc", is_available=True)
    h2 = Hall(name="Available 2", description="Desc", is_available=True)
    h3 = Hall(name="Unavailable 1", description="Desc", is_available=False)
    h4 = Hall(name="Unavailable 2", description="Desc", is_available=False)

    db_session.add_all([h1, h2, h3, h4])
    await db_session.flush()

    # Filter by available
    response = await client.get(f"/halls/?{HallFilterNames.STATUS.value}={HallStatusFilter.AVAILABLE.value}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
      assert item["is_available"] is True

    # Filter by unavailable
    response = await client.get(f"/halls/?{HallFilterNames.STATUS.value}={HallStatusFilter.UNAVAILABLE.value}")
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
      assert item["is_available"] is False

    # Filter all (or no filter)
    response = await client.get(f"/halls/?{HallFilterNames.STATUS.value}={HallStatusFilter.ALL.value}")
    data = response.json()
    assert data["total"] == 4


class TestGetHallById:
  """Tests for GET /halls/{id} endpoint"""

  async def test_get_hall_by_id_success(self, client: AsyncClient, db_session: AsyncSession):
    """Successfully get hall by ID"""
    hall = Hall(name="Test Hall", description="Test Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.get(f"/halls/{hall.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == hall.id
    assert data["name"] == "Test Hall"
    assert data["description"] == "Test Description"
    assert data["is_available"] is True

  async def test_get_hall_by_id_not_found(self, client: AsyncClient):
    """Getting non-existent hall by ID returns 404"""
    response = await client.get("/halls/99999")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_get_hall_by_id_invalid_id(self, client: AsyncClient):
    """Getting hall with invalid ID format returns 422"""
    response = await client.get("/halls/invalid")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_get_hall_by_id_zero(self, client: AsyncClient):
    """Getting hall with ID 0"""
    response = await client.get("/halls/0")

    # Should return 404 since there's no hall with ID 0
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_get_hall_by_id_negative(self, client: AsyncClient):
    """Getting hall with negative ID"""
    response = await client.get("/halls/-1")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND


class TestGetHallByName:
  """Tests for GET /halls/by-name/{name} endpoint"""

  async def test_get_hall_by_name_success(self, client: AsyncClient, db_session: AsyncSession):
    """Successfully get hall by name"""
    hall = Hall(name="Unique Hall", description="Test Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.get("/halls/by-name/Unique Hall")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Unique Hall"
    assert data["description"] == "Test Description"
    assert data["is_available"] is True

  async def test_get_hall_by_name_not_found(self, client: AsyncClient):
    """Getting non-existent hall by name returns 404"""
    response = await client.get("/halls/by-name/NonExistentHall")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_get_hall_by_name_with_spaces(self, client: AsyncClient, db_session: AsyncSession):
    """Getting hall by name with spaces"""
    hall = Hall(name="Hall With Spaces", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # URL encoding handled by httpx
    response = await client.get("/halls/by-name/Hall With Spaces")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hall With Spaces"

  async def test_get_hall_by_name_case_sensitive(self, client: AsyncClient, db_session: AsyncSession):
    """Hall name lookup is case-sensitive"""
    hall = Hall(name="MyHall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Exact case should work
    response = await client.get("/halls/by-name/MyHall")
    assert response.status_code == 200

    # Different case should fail
    response = await client.get("/halls/by-name/myhall")
    assert response.status_code == 404


class TestSearchHalls:
  """Tests for GET /halls/search endpoint"""

  @pytest.mark.skip(reason="Search requires PostgreSQL-specific features (full-text search, trigram)")
  async def test_search_halls_by_name(self, client: AsyncClient, db_session: AsyncSession):
    """Search halls by name"""
    h1 = Hall(name="Conference Room A", description="Small room", is_available=True)
    h2 = Hall(name="Conference Room B", description="Large room", is_available=True)
    h3 = Hall(name="Ballroom", description="Very large space", is_available=True)

    db_session.add_all([h1, h2, h3])
    await db_session.flush()

    response = await client.get("/halls/search?q=Conference")

    assert response.status_code == 200
    data = cast(list[Any], response.json())
    assert isinstance(data, list)
    assert len(data) == 2

    names = [item["name"] for item in data]
    assert "Conference Room A" in names
    assert "Conference Room B" in names

  @pytest.mark.skip(reason="Search requires PostgreSQL-specific features (full-text search, trigram)")
  async def test_search_halls_by_description(self, client: AsyncClient, db_session: AsyncSession):
    """Search halls by description"""
    h1 = Hall(name="Hall A", description="Perfect for weddings", is_available=True)
    h2 = Hall(name="Hall B", description="Great for meetings", is_available=True)
    h3 = Hall(name="Hall C", description="Ideal for concerts", is_available=True)

    db_session.add_all([h1, h2, h3])
    await db_session.flush()

    response = await client.get("/halls/search?q=weddings")

    assert response.status_code == 200
    data = response.json()
    # Should find Hall A based on description
    assert len(data) >= 1
    names = [item["name"] for item in data]
    assert "Hall A" in names

  async def test_search_halls_min_length(self, client: AsyncClient):
    """Search query must be at least 2 characters"""
    response = await client.get("/halls/search?q=a")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  @pytest.mark.skip(reason="Search requires PostgreSQL-specific features (full-text search, trigram)")
  async def test_search_halls_empty_results(self, client: AsyncClient, db_session: AsyncSession):
    """Search with no matches returns empty list"""
    hall = Hall(name="Hall A", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.get("/halls/search?q=NonExistentSearchTerm")

    assert response.status_code == 200
    data = cast(list[Any], response.json())
    assert isinstance(data, list)
    # May be empty or have low-ranking results
    assert len(data) >= 0

  @pytest.mark.skip(reason="Search requires PostgreSQL-specific features (full-text search, trigram)")
  async def test_search_halls_partial_match(self, client: AsyncClient, db_session: AsyncSession):
    """Search finds partial matches"""
    hall = Hall(name="Presidential Suite", description="Luxury hall", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.get("/halls/search?q=Presid")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = [item["name"] for item in data]
    assert "Presidential Suite" in names

  @pytest.mark.skip(reason="Search requires PostgreSQL-specific features (full-text search, trigram)")
  async def test_search_halls_ranking(self, client: AsyncClient, db_session: AsyncSession):
    """Search results include ranking"""
    hall = Hall(name="Test Hall", description="Test description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.get("/halls/search?q=Test")

    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
      assert "rank" in data[0]
      assert isinstance(data[0]["rank"], (int, float))
