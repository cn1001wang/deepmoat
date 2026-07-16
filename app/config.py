from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Secrets deliberately have no repository defaults.  The database fallback is
    only convenient for local development; production deployments must provide
    DATABASE_URL through `.env` or the process environment.
    """

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://postgres@localhost:5432/deepmoat"
    TUSHARE_TOKEN: str = ""
    PROJECT_NAME: str = "DeepMoat"
    CORS_ORIGINS: str = "http://localhost:5100,http://127.0.0.1:5100"

    AI_API_URL: str = ""
    AI_API_KEY: str = ""
    AI_API_MODEL: str = "claude-sonnet-4-20250514"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
