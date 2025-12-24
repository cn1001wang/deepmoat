from fastapi import FastAPI
from app.api.v1.api import api_router # 汇总后的路由
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}