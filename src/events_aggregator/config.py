import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER") or os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_DATABASE_NAME")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
EVENTS_PROVIDER_BASE_URL = os.getenv("EVENTS_PROVIDER_BASE_URL")
EVENTS_PROVIDER_API_KEY = os.getenv("EVENTS_PROVIDER_API_KEY")

env_dict = {
    "POSTGRES_USER": POSTGRES_USER,
    "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
    "POSTGRES_DB": POSTGRES_DB,
    "POSTGRES_HOST": POSTGRES_HOST,
    "POSTGRES_PORT": POSTGRES_PORT,
    "EVENTS_PROVIDER_BASE_URL": EVENTS_PROVIDER_BASE_URL,
    "EVENTS_PROVIDER_API_KEY": EVENTS_PROVIDER_API_KEY,
}

for env_key, env_value in env_dict.items():
    if not env_value:
        raise ValueError(f"Переменная окружения {env_key} не задана")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
