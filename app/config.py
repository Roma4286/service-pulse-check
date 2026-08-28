from pathlib import Path

from dotenv import load_dotenv
import os
from pydantic.v1 import BaseSettings

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

if not ENV_PATH.is_file():
    raise RuntimeError(
        f".env file not found at {ENV_PATH}. Copy .env.example to .env and fill in the values."
    )

load_dotenv(dotenv_path=ENV_PATH)

REQUIRED_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REDIS_URL",
)

missing_env_vars = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
if missing_env_vars:
    raise RuntimeError(
        f"Missing required environment variables in {ENV_PATH}: {', '.join(missing_env_vars)}"
    )

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
