from app.models.models import FinaIndicator
from .base_bulk_upsert import bulk_upsert
import pandas as pd

def save_fina_indicator( df: pd.DataFrame):
    bulk_upsert(
        table=FinaIndicator.__table__,
        df=df,
        conflict_cols=["ts_code", "ann_date", "end_date"]
    )
