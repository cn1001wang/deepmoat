import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import FinaMainbz
from .base_bulk_upsert import bulk_upsert


def save_fina_mainbz(df: pd.DataFrame):
    if df is None or df.empty:
        return

    work = df.copy()

    # 对部分旧数据做兜底，避免主键为空导致整行被丢弃。
    if "type" not in work.columns:
        work["type"] = "P"
    work["type"] = work["type"].fillna("P").astype(str)
    work.loc[work["type"] == "", "type"] = "P"

    if "bz_item" not in work.columns:
        work["bz_item"] = "UNKNOWN"
    work["bz_item"] = work["bz_item"].fillna("UNKNOWN").astype(str)
    work.loc[work["bz_item"] == "", "bz_item"] = "UNKNOWN"

    bulk_upsert(
        table=FinaMainbz.__table__,
        df=work,
        conflict_cols=["ts_code", "end_date", "type", "bz_item"],
    )


def check_fina_mainbz_exists(db: Session, ts_code: str, bz_type: str | None = None) -> bool:
    query = db.query(FinaMainbz).filter(FinaMainbz.ts_code == ts_code)
    if bz_type:
        query = query.filter(FinaMainbz.type == bz_type)
    return query.first() is not None
