from app.models.models import FinaAudit
from sqlalchemy.orm import Session
from .base_bulk_upsert import bulk_upsert
import pandas as pd


def save_fina_audit(df: pd.DataFrame):
    bulk_upsert(
        table=FinaAudit.__table__,
        df=df,
        conflict_cols=["ts_code", "end_date"]
    )


def get_fina_audit(ts_code: str, db: Session) -> list[FinaAudit]:
    return (
        db.query(FinaAudit)
        .filter(FinaAudit.ts_code == ts_code)
        .order_by(FinaAudit.end_date.desc())
        .all()
    )


def check_fina_audit_exists(db: Session, ts_code: str) -> bool:
    return db.query(FinaAudit).filter(FinaAudit.ts_code == ts_code).first() is not None
