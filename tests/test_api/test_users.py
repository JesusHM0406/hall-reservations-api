from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.models.user import User
from app.schemas.user import UserCreate

class TestCreateUser:
  async def test_create_user_success(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="name",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "name"

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count + 1

  async def test_create_user_duplicated(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    fake_user = User(
      name="name",
      pw_hash="fakepasswordhash"
    )

    db_session.add(fake_user)
    await db_session.flush()

    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    assert before_total_count > 0

    new_user_schema = UserCreate(
      name="name",
      password="newpassword",
      password_confirm="newpassword"
    )

    response = await client.post("/users/", json=new_user_schema.model_dump())

    assert response.status_code == 409

    data = response.json()
    assert data["message"] == ErrorMessages.DUPLICATED_USERNAME

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_password_mismatch(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="name",
      password="password",
      password_confirm="otherpassword"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 400

    data = response.json()
    assert data["message"] == ErrorMessages.PASSWORDS_MISMATCH

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_white_space_name(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="     ",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 400

    data = response.json()
    assert data["message"] == ErrorMessages.EMPTY_NAME

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count

  async def test_create_user_white_space_name_success(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    before_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    before_total_count = before_total_count_res.scalar() or 0

    user_schema = UserCreate(
      name="  name   ",
      password="password",
      password_confirm="password"
    )

    response = await client.post("/users/", json=user_schema.model_dump())
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "name"

    after_total_count_res = await db_session.execute(
      select(func.count())
      .select_from(User)
    )
    after_total_count = after_total_count_res.scalar() or 0
    assert after_total_count == before_total_count + 1
