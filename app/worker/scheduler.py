from rocketry import Rocketry
from rocketry.conds import hourly

from app.crud.reservation import crud_finish_reservations
from app.db.session import AsyncSessionLocal

app_rocketry = Rocketry(execution="async")

@app_rocketry.task(hourly)
async def finish_reservations():
  async with AsyncSessionLocal() as db:
    async with db.begin():
      await crud_finish_reservations(db=db)
