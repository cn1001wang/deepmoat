from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

# 假设你的项目结构中 database 提供了 SessionLocal
from app.db.session import get_db
from app.service import trend_service
from app.crud.crud_trend import get_stock_basic

# 创建路由，替代 Flask 的 Blueprint
router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

@router.get("/trends/{ts_code}")
async def get_trends(ts_code: str, db: Session = Depends(get_db)):
    """
    接口1：趋势数据
    """
    stock = get_stock_basic(db, ts_code)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    trends = trend_service.get_stock_trends(db, ts_code)
    
    # 确保 trends 是可变字典以便添加字段
    result = dict(trends)
    result['stock_name'] = stock.name
    
    return result

@router.get("/indicators/{ts_code}")
async def get_indicators(ts_code: str, db: Session = Depends(get_db)):
    """
    接口2：详细指标
    """
    data = trend_service.get_detailed_indicators(db, ts_code)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
        
    return {
        "ts_code": ts_code, 
        "data": data
    }