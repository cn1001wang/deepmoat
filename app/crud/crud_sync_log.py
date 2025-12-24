from common.database import SessionLocal
from common.models import Income, BalanceSheet, CashFlow, FinanceSyncLog
from sqlalchemy import func

TABLE_MODEL = {
    "income": Income,
    "balancesheet": BalanceSheet,
    "cashflow": CashFlow,
}


def get_db_max_end_date(ts_code, table_name: str):
    # ⭐ 防御：如果是 Row / tuple，取第一个元素
    if not isinstance(ts_code, str):
        ts_code = ts_code[0]

    session = SessionLocal()
    try:
        model = TABLE_MODEL[table_name]
        return (
            session.query(func.max(model.end_date))
            .filter(model.ts_code == ts_code)
            .scalar()
        )
    finally:
        session.close()



def update_sync_log(ts_code: str, table_name: str, end_date: str):
    session = SessionLocal()
    try:
        obj = FinanceSyncLog(
            ts_code=ts_code,
            table_name=table_name,
            last_sync_end_date=end_date,
        )
        session.merge(obj)
        session.commit()
    finally:
        session.close()
