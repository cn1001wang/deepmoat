from common.database import SessionLocal
from common.models import StockBasic
import pandas as pd

def save_stock_basic(df: pd.DataFrame):
    session = SessionLocal()
    try:
        for _, row in df.iterrows():
            obj = StockBasic(
                ts_code=row["ts_code"],
                symbol=row["symbol"],
                name=row["name"],
                fullname=row.get("fullname"),
                ennname=row.get("ennname"),
                cnspell=row.get("cnspell"),
                area=row.get("area"),
                industry=row.get("industry"),
                market=row.get("market"),
                exchange=row.get("exchange"),
                curr_type=row.get("curr_type"),
                list_status=row.get("list_status"),
                list_date=row.get("list_date"),
                delist_date=row.get("delist_date"),
                is_hs=row.get("is_hs"),
                act_name=row.get("act_name"),
                act_ent_type=row.get("act_ent_type"),
            )
            session.merge(obj)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def get_stock_basic_all():
    session = SessionLocal()
    try:
        return session.query(StockBasic).all()
    finally:
        session.close()