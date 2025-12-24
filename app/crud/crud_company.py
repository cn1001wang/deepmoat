from common.database import SessionLocal
from common.models import StockCompany
import pandas as pd
import math

def save_stock_company(df: pd.DataFrame):
    session = SessionLocal()

    try:
        for _, row in df.iterrows():
            obj = StockCompany(
                ts_code=row["ts_code"],
                com_name=row.get("com_name"),
                com_id=row.get("com_id"),
                exchange=row.get("exchange"),
                chairman=row.get("chairman"),
                manager=row.get("manager"),
                secretary=row.get("secretary"),
                reg_capital=_safe_float(row.get("reg_capital")),
                setup_date=row.get("setup_date"),
                province=row.get("province"),
                city=row.get("city"),
                website=row.get("website"),
                email=row.get("email"),
                employees=_safe_int(row.get("employees")),
            )
            session.merge(obj)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def _safe_float(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v)


def _safe_int(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return int(v)

def get_all_listed_companies():
    session = SessionLocal()
    try:
        rows = session.query(
            StockCompany.ts_code,
            StockCompany.setup_date
        ).filter(StockCompany.exchange != "SZSE").all()

        # ⭐ 显式转成 tuple[str, str]
        return [(r.ts_code, r.setup_date) for r in rows]
    finally:
        session.close()

def get_stock_company():
    session = SessionLocal()
    try:
        rows = session.query(
            StockCompany
        ).all()

        return rows
    finally:
        session.close()