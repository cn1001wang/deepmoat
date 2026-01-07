from sqlalchemy.dialects.postgresql import insert
from app.db.session import engine
import pandas as pd


def bulk_upsert(table, df: pd.DataFrame, conflict_cols: list[str]):
    """
    PostgreSQL 批量 upsert（insert or update）

    规则：
    - conflict_cols 中任意字段为空 → 丢弃该行
    - 同一批次 conflict key 去重（保留最后一条）
    """

    # 0️⃣ 无数据直接返回
    if df is None or df.empty:
        return

    # 1️⃣ 只保留表中真实存在的列
    table_cols = {c.name for c in table.columns}
    df = df[[c for c in df.columns if c in table_cols]]

    # 2️⃣ 🔥 丢弃 conflict key 中有空值的行
    # NaN / None 都会被识别
    df = df.dropna(subset=conflict_cols)

    if df.empty:
        return

    # 3️⃣ 🔥 同一批次 conflict key 去重（防止 ON CONFLICT 二次命中）
    # 默认保留“最后一条”（通常是最新抓取的）
    df = df.drop_duplicates(subset=conflict_cols, keep="last")

    if df.empty:
        return

    # 4️⃣ NaN → None（数据库只认 NULL）
    df = df.astype(object)
    records = df.where(pd.notnull(df), None).to_dict("records")

    if not records:
        return

    # 5️⃣ 构造 INSERT
    stmt = insert(table).values(records)

    # 6️⃣ 构造 UPDATE（排除冲突字段）
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in table.columns
        if c.name not in conflict_cols
    }

    # 7️⃣ ON CONFLICT DO UPDATE
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_cols,
        set_=update_cols
    )

    # 8️⃣ 执行
    with engine.begin() as conn:
        conn.execute(stmt)
