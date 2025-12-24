from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.moat_engine import MoatEngine
from app.services.tushare_adapter import TushareAdapter # 封装的抓取逻辑

router = APIRouter()

@router.get("/table")
def get_finance_table(
    ts_code: str, 
    years: int = 6, 
    db: Session = Depends(get_db)
):
    # 1. 抓取层/中间层：获取原始数据
    try:
        # 实际开发中，这里可以优先从本地 db 读，没有再调 Tushare
        income_df = TushareAdapter.get_income(ts_code) 
        balance_df = TushareAdapter.get_balance(ts_code)
        cash_df = TushareAdapter.get_cash(ts_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据抓取失败: {str(e)}")

    # 2. 算法层：执行智能评级与指标计算
    payload = MoatEngine.build_metrics_table(income_df, balance_df, cash_df)

    if not payload["periods"]:
        raise HTTPException(status_code=404, detail="未找到财报数据")

    return {"code": 200, "data": payload}