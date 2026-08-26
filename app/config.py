from dotenv import load_dotenv
import os
from pydantic.v1 import BaseSettings

load_dotenv()

PG_HOST = os.getenv('POSTGRES_HOST')
PG_PORT = os.getenv('POSTGRES_PORT')
PG_NAME = os.getenv('POSTGRES_DB')
PG_USER = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')

REDIS_URL = os.environ.get("REDIS_URL")

class Settings(BaseSettings):
    pg_url: str = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"

    redis_url: str = REDIS_URL

settings = Settings()