from app.models.models import FinaIndicator
from sqlalchemy.orm import Session
from .base_bulk_upsert import bulk_upsert
import pandas as pd

def save_fina_indicator( df: pd.DataFrame):
    bulk_upsert(
        table=FinaIndicator.__table__,
        df=df,
        conflict_cols=["ts_code", "ann_date", "end_date"]
    )

def get_fina_indicator(ann_date: str, ts_code: str, db: Session):
    """
    获取所有财务指标对象
    """
    query = db.query(FinaIndicator)
    if ann_date:
        query = query.filter(FinaIndicator.ann_date == ann_date)
    if ts_code:
        query = query.filter(FinaIndicator.ts_code == ts_code)
    return query.all()