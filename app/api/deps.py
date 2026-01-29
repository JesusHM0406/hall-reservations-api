from fastapi import Depends
from typing import AsyncGenerator, Annotated
from app.db.session import AsyncSession, AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    yield session

DBDep = Annotated[AsyncSession, Depends(get_db)]
