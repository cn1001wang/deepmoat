from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:123456@localhost:5432/testdb"
    TUSHARE_TOKEN: str = ""
    PROJECT_NAME: str = "DeepMoat"

    AI_API_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-20250514"

    class Config:
        env_file = ".env"

settings = Settings()