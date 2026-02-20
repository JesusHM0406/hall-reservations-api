import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

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
