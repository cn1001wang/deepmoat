from sqlalchemy.dialects.postgresql import insert
from app.db.session import engine
import pandas as pd


def bulk_upsert(table, df: pd.DataFrame, conflict_cols: list[str]):
    if df is None or df.empty:
        return

    # ① 只保留“表中存在的列”
    table_cols = set(c.name for c in table.columns)
    df = df[[c for c in df.columns if c in table_cols]]

    # ② NaN → None
    records = df.where(pd.notnull(df), None).to_dict("records")

    if not records:
        return

    stmt = insert(table).values(records)

    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in table.columns
        if c.name not in conflict_cols
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_cols,
        set_=update_cols
    )

    with engine.begin() as conn:
        conn.execute(stmt)
