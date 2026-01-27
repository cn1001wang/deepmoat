from app.models.models import DailyBasic
from .base_bulk_upsert import bulk_upsert
from sqlalchemy.orm import Session
import pandas as pd

def save_daily_basic(df: pd.DataFrame):
    bulk_upsert(
        table=DailyBasic.__table__,
        df=df,
        conflict_cols=["ts_code", "trade_date"]
    )

def get_daily_basic(trade_date: str, ts_code: str, db: Session):
    """
    获取所有每日基础数据对象
    """
    query = db.query(DailyBasic)
    if ts_code:
        query = query.filter(DailyBasic.ts_code == ts_code)
    if trade_date:
        query = query.filter(DailyBasic.trade_date == trade_date)
    return query.all()