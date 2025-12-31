from sqlalchemy.dialects.postgresql import insert
from app.db.session import engine
import pandas as pd


def bulk_upsert(table, df: pd.DataFrame, conflict_cols: list[str]):
    """
    PostgreSQL 批量 upsert（insert or update）

    :param table: SQLAlchemy Table 对象，如 Model.__table__
    :param df: 要写入的数据，pandas DataFrame
    :param conflict_cols: 冲突字段（唯一键 / 主键），如 ["ts_code", "trade_date"]
    """

    # 0️⃣ 无数据直接返回，避免空写入
    if df is None or df.empty:
        return

    # 1️⃣ 只保留“数据库表中真实存在的列”
    # 防止 DataFrame 多列导致 SQL 报错
    table_cols = set(c.name for c in table.columns)
    df = df[[c for c in df.columns if c in table_cols]]

    # 2️⃣ 将 DataFrame 中的 NaN 转为 None
    # PostgreSQL 不认识 NaN，只接受 NULL
    records = df.where(pd.notnull(df), None).to_dict("records")

    if not records:
        return

    # 3️⃣ 构造 INSERT 语句（一次性批量 values）
    stmt = insert(table).values(records)

    # 4️⃣ 构造 UPDATE 部分
    # 排除冲突列（主键不能被 update）
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in table.columns
        if c.name not in conflict_cols
    }

    # 5️⃣ ON CONFLICT DO UPDATE
    # 当 conflict_cols 冲突时，更新非主键字段
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_cols,
        set_=update_cols
    )

    # 6️⃣ 执行 SQL（事务自动提交 / 回滚）
    with engine.begin() as conn:
        conn.execute(stmt)
