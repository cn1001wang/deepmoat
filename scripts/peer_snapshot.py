import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]


def load_engine():
    load_dotenv(ROOT / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
    )
    return create_engine(database_url.replace("+psycopg2", ""))


def query_df(engine, sql: str, params: dict) -> pd.DataFrame:
    return pd.read_sql(text(sql), engine, params=params)


def resolve_stock(engine, query: str) -> dict:
    sql = """
    SELECT ts_code, symbol, name
    FROM stock_basic
    WHERE ts_code = :query OR symbol = :query OR name = :query
    ORDER BY ts_code
    LIMIT 1
    """
    df = query_df(engine, sql, {"query": query})
    if df.empty:
        fuzzy = query_df(
            engine,
            """
            SELECT ts_code, symbol, name
            FROM stock_basic
            WHERE name LIKE :kw
            ORDER BY ts_code
            LIMIT 1
            """,
            {"kw": f"%{query}%"},
        )
        if fuzzy.empty:
            raise ValueError(f"未找到标的: {query}")
        return fuzzy.iloc[0].to_dict()
    return df.iloc[0].to_dict()


def latest_annual(engine, ts_code: str) -> dict:
    income = query_df(
        engine,
        """
        SELECT end_date, total_revenue, n_income_attr_p
        FROM income
        WHERE ts_code = :ts_code
          AND report_type = '1'
          AND end_date LIKE '%1231'
        ORDER BY end_date DESC
        LIMIT 2
        """,
        {"ts_code": ts_code},
    )
    ind = query_df(
        engine,
        """
        SELECT DISTINCT ON (end_date) end_date, ann_date, roe, grossprofit_margin,
               netprofit_margin, debt_to_assets, roic
        FROM fina_indicator
        WHERE ts_code = :ts_code
          AND end_date LIKE '%1231'
        ORDER BY end_date DESC, ann_date DESC
        LIMIT 1
        """,
        {"ts_code": ts_code},
    )
    daily = query_df(
        engine,
        """
        SELECT trade_date, close, pe_ttm, pb, ps_ttm, total_mv
        FROM daily_basic
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        {"ts_code": ts_code},
    )

    row = {
        "end_date": None,
        "revenue_yoy": None,
        "profit_yoy": None,
        "roe": None,
        "roic": None,
        "grossprofit_margin": None,
        "netprofit_margin": None,
        "debt_to_assets": None,
        "trade_date": None,
        "close": None,
        "pe_ttm": None,
        "pb": None,
        "ps_ttm": None,
        "total_mv": None,
    }
    if not income.empty:
        curr = income.iloc[0]
        row["end_date"] = curr["end_date"]
        row["revenue"] = curr["total_revenue"]
        row["profit"] = curr["n_income_attr_p"]
        if len(income) > 1:
            prev = income.iloc[1]
            if prev["total_revenue"]:
                row["revenue_yoy"] = (curr["total_revenue"] - prev["total_revenue"]) / abs(prev["total_revenue"]) * 100
            if prev["n_income_attr_p"]:
                row["profit_yoy"] = (curr["n_income_attr_p"] - prev["n_income_attr_p"]) / abs(prev["n_income_attr_p"]) * 100
    if not ind.empty:
        row.update(ind.iloc[0].to_dict())
    if not daily.empty:
        row.update(daily.iloc[0].to_dict())
    return row


def fmt_num(value, scale=1.0, suffix="") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value) / scale:.2f}{suffix}"


def fmt_pct(value) -> str:
    return fmt_num(value, 1.0, "%")


def build_rows(engine, queries: list[str]) -> list[dict]:
    rows = []
    for query in queries:
        stock = resolve_stock(engine, query)
        metrics = latest_annual(engine, stock["ts_code"])
        rows.append(
            {
                "代码": stock["ts_code"],
                "名称": stock["name"],
                "估值日": metrics.get("trade_date"),
                "PE(TTM)": fmt_num(metrics.get("pe_ttm")),
                "PB": fmt_num(metrics.get("pb")),
                "PS(TTM)": fmt_num(metrics.get("ps_ttm")),
                "市值(亿)": fmt_num(metrics.get("total_mv"), 1e4),
                "年报期": metrics.get("end_date"),
                "营收增速": fmt_pct(metrics.get("revenue_yoy")),
                "净利增速": fmt_pct(metrics.get("profit_yoy")),
                "毛利率": fmt_pct(metrics.get("grossprofit_margin")),
                "净利率": fmt_pct(metrics.get("netprofit_margin")),
                "ROE": fmt_pct(metrics.get("roe")),
                "ROIC": fmt_pct(metrics.get("roic")),
                "资产负债率": fmt_pct(metrics.get("debt_to_assets")),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description="生成休闲零食可比公司快照")
    parser.add_argument(
        "queries",
        nargs="*",
        default=["盐津铺子", "甘源食品", "劲仔食品", "三只松鼠", "洽洽食品", "良品铺子"],
    )
    args = parser.parse_args()

    engine = load_engine()
    rows = build_rows(engine, args.queries)
    df = pd.DataFrame(rows)
    print(df.to_markdown(index=False))


if __name__ == "__main__":
    main()
