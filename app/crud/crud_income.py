from common.models import Income
from common.crud.base_bulk_upsert import bulk_upsert
from common.utils.df_utils import dedup_finance_df

def save_income_bulk(df):
    df = dedup_finance_df(df)

    bulk_upsert(
        Income.__table__,
        df,
        conflict_cols=["ts_code", "end_date", "report_type"]
    )
