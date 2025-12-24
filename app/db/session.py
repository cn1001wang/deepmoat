from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# 依赖注入：在 API 路由中使用
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()