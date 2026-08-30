from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str = Field(
        validation_alias=AliasChoices("POSTGRES_USER", "POSTGRES_USERNAME")
    )
    postgres_password: str
    postgres_db: str = Field(
        validation_alias=AliasChoices("POSTGRES_DB", "POSTGRES_DATABASE_NAME")
    )
    postgres_host: str
    postgres_port: int
    events_provider_base_url: str
    events_provider_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@"
    f"{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)
