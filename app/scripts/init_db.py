import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.getcwd())

from app.db.session import engine, Base
# 导入所有模型以确保它们被注册到 Base.metadata
from app.models import models 

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
