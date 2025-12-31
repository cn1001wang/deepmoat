from app.models.models import DailyBasic
from .base_bulk_upsert import bulk_upsert
import pandas as pd

def save_daily_basic(df: pd.DataFrame):
    bulk_upsert(
        table=DailyBasic.__table__,
        df=df,
        conflict_cols=["ts_code", "trade_date"]
    )
