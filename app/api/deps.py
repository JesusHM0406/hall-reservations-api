from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.db.session import AsyncSession, AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    yield session

DBDep = Annotated[AsyncSession, Depends(get_db)]
