import asyncio
from typing import Any, AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base_class import Base
from app.main import app
from app.utils.rate_limit import global_rate_limiter, login_rate_limiter, registration_rate_limiter

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
  DATABASE_URL,
  connect_args={"check_same_thread": False},
  poolclass=StaticPool
)

TestingSessionLocal = async_sessionmaker(
  autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest.fixture(scope="session")
def event_loop():
  """Create an event loop instance for each testing session."""
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database(event_loop: Any) -> AsyncGenerator[None, None]:
  """Create the tables before the tests and delete them at the end."""
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  yield
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
async def reset_all_rate_limiters():
  """Auto-reset all rate limiters before each test."""
  await global_rate_limiter.reset_all()
  await login_rate_limiter.reset_all()
  await registration_rate_limiter.reset_all()
  yield
  await global_rate_limiter.reset_all()
  await login_rate_limiter.reset_all()
  await registration_rate_limiter.reset_all()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
  """Fixture to get a clean DB session in each test."""
  async with engine.connect() as connection:
    transaction = await connection.begin()
    async with AsyncSession(bind=connection, expire_on_commit=False) as session:
      yield session
    await transaction.rollback()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
  """Fixture to create an HTTP client that uses the fake db."""

  async def _get_test_db():
    yield db_session

  app.dependency_overrides[get_db] = _get_test_db

  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    yield ac

  app.dependency_overrides.clear()