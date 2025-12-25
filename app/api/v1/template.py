# from fastapi import FastAPI, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List

# from . import models, schemas
# from .database import engine, get_db

# # 自动创建表结构
# models.Base.metadata.create_all(bind=engine)

# app = FastAPI(title="SwIndustry CRUD Demo")

# # --- CRUD 接口 ---

# # 1. 创建 (Create)
# @app.post("/industries/", response_model=schemas.SwIndustryResponse)
# def create_industry(item: schemas.SwIndustryCreate, db: Session = Depends(get_db)):
#     db_item = db.query(models.SwIndustry).filter(models.SwIndustry.index_code == item.index_code).first()
#     if db_item:
#         raise HTTPException(status_code=400, detail="Index code already registered")
    
#     new_industry = models.SwIndustry(**item.model_dump())
#     db.add(new_industry)
#     db.commit()
#     db.refresh(new_industry)
#     return new_industry

# # 2. 读取全部 (Read List)
# @app.get("/industries/", response_model=List[schemas.SwIndustryResponse])
# def read_industries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     return db.query(models.SwIndustry).offset(skip).limit(limit).all()

# # 3. 读取单个 (Read One)
# @app.get("/industries/{index_code}", response_model=schemas.SwIndustryResponse)
# def read_industry(index_code: str, db: Session = Depends(get_db)):
#     db_item = db.query(models.SwIndustry).filter(models.SwIndustry.index_code == index_code).first()
#     if not db_item:
#         raise HTTPException(status_code=404, detail="Industry not found")
#     return db_item

# # 4. 更新 (Update)
# @app.put("/industries/{index_code}", response_model=schemas.SwIndustryResponse)
# def update_industry(index_code: str, item: schemas.SwIndustryBase, db: Session = Depends(get_db)):
#     db_item = db.query(models.SwIndustry).filter(models.SwIndustry.index_code == index_code).first()
#     if not db_item:
#         raise HTTPException(status_code=404, detail="Industry not found")
    
#     for key, value in item.model_dump().items():
#         setattr(db_item, key, value)
    
#     db.commit()
#     db.refresh(db_item)
#     return db_item

# # 5. 删除 (Delete)
# @app.delete("/industries/{index_code}")
# def delete_industry(index_code: str, db: Session = Depends(get_db)):
#     db_item = db.query(models.SwIndustry).filter(models.SwIndustry.index_code == index_code).first()
#     if not db_item:
#         raise HTTPException(status_code=404, detail="Industry not found")
    
#     db.delete(db_item)
#     db.commit()
#     return {"message": "Successfully deleted"}