from common.models import BalanceSheet
from common.crud.base_bulk_upsert import bulk_upsert
from common.utils.df_utils import dedup_finance_df

def save_balancesheet_bulk(df):
    df = dedup_finance_df(df)

    bulk_upsert(
        BalanceSheet.__table__,
        df,
        conflict_cols=["ts_code", "end_date", "report_type"]
    )
