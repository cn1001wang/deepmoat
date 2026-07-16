from fastapi import FastAPI
from app.api.v1 import analysis_router, raw_data_router, user_data_router, ai_valuation_router, screener_router
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from sqlalchemy import text
from app.db.session import engine

app = FastAPI(title=settings.PROJECT_NAME)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis_router, prefix="/api")
app.include_router(raw_data_router, prefix="/api")
app.include_router(user_data_router, prefix="/api")
app.include_router(ai_valuation_router, prefix="/api")
app.include_router(screener_router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}


@app.get("/health")
def health():
    """Liveness probe: confirms that the API process is accepting requests."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/ready")
def ready():
    """Readiness probe: confirms that PostgreSQL is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}

    
# ------------------------
# 启动配置
# ------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5005)),
        reload=True,
    )
