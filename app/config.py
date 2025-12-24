from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 默认值，实际从 .env 覆盖
    DATABASE_URL: str = "postgresql+psycopg2://postgres:123456@localhost:5432/testdb"
    TUSHARE_TOKEN: str = ""
    PROJECT_NAME: str = "DeepMoat"

    class Config:
        env_file = ".env"

settings = Settings()