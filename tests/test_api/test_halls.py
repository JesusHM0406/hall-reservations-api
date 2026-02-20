from httpx import AsyncClient

async def test_get_halls_smoke(client: AsyncClient):
  response = await client.get("/halls/")

  # If this returns 200, it means that:
  # 1. FastAPI loads correctly.
  # 3. SQLite in memory has been created correctly.
  assert response.status_code == 200

  data = response.json()

  assert "items" in data
  assert isinstance(data["items"], list)
  # The list should be empty because the database is clean.
  assert data["total"] == 0
