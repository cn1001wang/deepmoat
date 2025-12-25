from fastapi import FastAPI
from app.api.v1 import analysis_router, raw_data_router # 汇总后的路由
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.PROJECT_NAME)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis_router, prefix="/api")
app.include_router(raw_data_router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

    
# ------------------------
# 启动配置
# ------------------------
if __name__ == "__main__":
    import uvicorn
    # 使用 uv run python main.py 启动或直接用 uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)