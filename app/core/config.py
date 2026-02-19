import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
  PROJECT_NAME: str = "Hall Reservations API"
  PROJECT_VERSION: str = "0.0.1"
  DATABASE_URL: str = os.environ["DATABASE_URL"]
  SECRET_KEY: str = os.environ["SECRET_KEY"]
  ALGORITHM: str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
  ALLOWED_ORIGINS: str = os.environ["ALLOWED_ORIGINS"]
  PAGINATION_LIMIT_PER_PAGE: int = 10
  SEARCH_LIMIT: int = 10

settings = Settings()
