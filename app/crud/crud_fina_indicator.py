from app.models.models import FinaIndicator
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from .base_bulk_upsert import bulk_upsert
import pandas as pd

def save_fina_indicator( df: pd.DataFrame):
    bulk_upsert(
        table=FinaIndicator.__table__,
        df=df,
        conflict_cols=["ts_code", "ann_date", "end_date"]
    )

def get_fina_indicator(ann_date: str, end_date: str, ts_code: str, db: Session):
    """
    获取所有财务指标对象
    """
    if end_date and not ann_date:
        latest_period_query = (
            db.query(
                FinaIndicator.ts_code.label("ts_code"),
                func.max(FinaIndicator.end_date).label("end_date"),
            )
            .filter(FinaIndicator.end_date <= end_date)
        )
        if ts_code:
            latest_period_query = latest_period_query.filter(FinaIndicator.ts_code == ts_code)
        latest_period = latest_period_query.group_by(FinaIndicator.ts_code).subquery()

        latest_ann_date = (
            db.query(
                FinaIndicator.ts_code.label("ts_code"),
                FinaIndicator.end_date.label("end_date"),
                func.max(FinaIndicator.ann_date).label("ann_date"),
            )
            .join(
                latest_period,
                and_(
                    FinaIndicator.ts_code == latest_period.c.ts_code,
                    FinaIndicator.end_date == latest_period.c.end_date,
                ),
            )
            .group_by(FinaIndicator.ts_code, FinaIndicator.end_date)
            .subquery()
        )

        return (
            db.query(FinaIndicator)
            .join(
                latest_ann_date,
                and_(
                    FinaIndicator.ts_code == latest_ann_date.c.ts_code,
                    FinaIndicator.end_date == latest_ann_date.c.end_date,
                    FinaIndicator.ann_date == latest_ann_date.c.ann_date,
                ),
            )
            .all()
        )

    query = db.query(FinaIndicator)
    if ann_date:
        query = query.filter(FinaIndicator.ann_date == ann_date)
    if ts_code:
        query = query.filter(FinaIndicator.ts_code == ts_code)
    if end_date:
        query = query.filter(FinaIndicator.end_date == end_date)
    return query.all()

def check_fina_indicator_exists(db: Session, ts_code: str) -> bool:
    return db.query(FinaIndicator).filter(FinaIndicator.ts_code == ts_code).first() is not None
