import asyncio
from app.crud.reservation import crud_finish_reservations
from app.db.session import AsyncSessionLocal

async def clean_expired_reservations():
  while True:
    print("--- [TASK] Checking expired reservations ---")
    try:
      async with AsyncSessionLocal() as db:
        async with db.begin():
          await crud_finish_reservations(db=db)
      print("--- [TASK] Cleaning completed successfully ---")
    except Exception as e:
      print(f"--- [TASK] Task error: {e} ---")

    await asyncio.sleep(3600)
