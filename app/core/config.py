import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
  PROJECT_NAME: str = "Hall Reservations API"
  PROJECT_VERSION: str = "0.0.1"
  DATABASE_URL: str = os.environ["DATABASE_URL"]

settings = Settings()