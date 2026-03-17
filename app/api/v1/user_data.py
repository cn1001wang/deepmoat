"""
用户股票数据 API
"""
from typing import List

from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import UserStockData
from app.schemas.stock_shcemes import UserStockDataRead, UserStockDataUpdate
from app.utils.api_utils import ok, ResponseOk

router = APIRouter(
    tags=["user_data"]
)


@router.get("/user_data/{ts_code}", response_model=ResponseOk[UserStockDataRead])
def get_user_data(
    ts_code: str = Path(..., description="股票代码"),
    db: Session = Depends(get_db)
):
    db_item = db.query(UserStockData).filter(UserStockData.ts_code == ts_code).first()
    if not db_item:
        return ok({"tsCode": ts_code, "remark": "", "tags": []})
    
    tags = db_item.tags.split(",") if db_item.tags else []
    return ok({"tsCode": db_item.ts_code, "remark": db_item.remark, "tags": tags})


@router.post("/user_data/{ts_code}", response_model=ResponseOk[UserStockDataRead])
def update_user_data(
    ts_code: str = Path(..., description="股票代码"),
    data: UserStockDataUpdate = Body(..., description="更新数据"),
    db: Session = Depends(get_db)
):
    db_item = db.query(UserStockData).filter(UserStockData.ts_code == ts_code).first()
    
    tags_str = ",".join(data.tags) if data.tags else ""
    
    if not db_item:
        db_item = UserStockData(ts_code=ts_code, remark=data.remark, tags=tags_str)
        db.add(db_item)
    else:
        db_item.remark = data.remark
        db_item.tags = tags_str
    
    db.commit()
    db.refresh(db_item)
    
    tags = db_item.tags.split(",") if db_item.tags else []
    return ok({"tsCode": db_item.ts_code, "remark": db_item.remark, "tags": tags})


@router.get("/tags/history", response_model=ResponseOk[List[str]])
def get_tags_history(db: Session = Depends(get_db)):
    # Get all tags and distinct them
    items = db.query(UserStockData.tags).filter(UserStockData.tags != None).all()
    all_tags = set()
    for item in items:
        if item.tags:
            for tag in item.tags.split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
    return ok(list(all_tags))


@router.get("/user_data_all", response_model=ResponseOk[List[UserStockDataRead]])
def get_all_user_data(db: Session = Depends(get_db)):
    items = db.query(UserStockData).all()
    res = []
    for item in items:
        tags = item.tags.split(",") if item.tags else []
        res.append({"tsCode": item.ts_code, "remark": item.remark, "tags": tags})
    return ok(res)
