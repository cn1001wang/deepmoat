#!/usr/bin/env python3
"""
作用：
按产品关键字查询 `fina_mainbz` 表中近五个年度报告期的主营业务数据，
按公司汇总展示收入、利润、成本、毛利率、收入同比，并计算可用区间 CAGR。

示例：
uv run python scripts/查询主营业务近五年.py --keyword 储能系统
uv run python scripts/查询主营业务近五年.py --keyword 光伏逆变器
"""

import argparse
import os
from collections import defaultdict

import pandas as pd
from sqlalchemy import create_engine, text


DEFAULT_DB = "postgresql+psycopg2://postgres:123456@localhost:5432/testdb"


def get_engine():
    database_url = os.getenv("DATABASE_URL", DEFAULT_DB).replace("+psycopg2", "")
    return create_engine(database_url)


def query_main_business(engine, keyword: str) -> pd.DataFrame:
    sql = text(
        """
        SELECT
            f.ts_code,
            COALESCE(s.name, '') AS name,
            f.end_date,
            f.bz_item,
            f.bz_sales,
            f.bz_profit,
            f.bz_cost
        FROM fina_mainbz f
        LEFT JOIN stock_basic s ON s.ts_code = f.ts_code
        WHERE f.type = 'P'
          AND RIGHT(f.end_date, 4) = '1231'
          AND f.end_date IN (
              SELECT DISTINCT end_date
              FROM fina_mainbz
              WHERE type = 'P'
                AND RIGHT(end_date, 4) = '1231'
                AND bz_item LIKE :pattern
              ORDER BY end_date DESC
              LIMIT 5
          )
          AND f.bz_item LIKE :pattern
        ORDER BY f.ts_code, f.end_date, f.bz_item
        """
    )
    return pd.read_sql(sql, engine, params={"pattern": f"%{keyword}%"})


def merge_company_year_rows(df: pd.DataFrame) -> pd.DataFrame:
    product_names = (
        df.groupby(["ts_code", "name", "end_date"])["bz_item"]
        .apply(lambda items: " / ".join(sorted(set(items))))
        .reset_index()
    )

    numeric_rows = (
        df.drop_duplicates(["ts_code", "end_date", "bz_sales", "bz_profit", "bz_cost"])
        .groupby(["ts_code", "name", "end_date"], as_index=False)[["bz_sales", "bz_profit", "bz_cost"]]
        .sum()
    )

    merged = numeric_rows.merge(product_names, on=["ts_code", "name", "end_date"], how="left")
    merged["year"] = merged["end_date"].str[:4].astype(int)
    merged = merged.sort_values(["ts_code", "year"])
    merged["sales_yi"] = merged["bz_sales"] / 1e8
    merged["profit_yi"] = merged["bz_profit"] / 1e8
    merged["cost_yi"] = merged["bz_cost"] / 1e8
    merged["gross_margin_pct"] = merged["bz_profit"] / merged["bz_sales"] * 100
    merged["yoy_pct"] = merged.groupby("ts_code")["sales_yi"].pct_change() * 100
    return merged


def build_cagr_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ts_code, name), sub in df.groupby(["ts_code", "name"]):
        sub = sub.sort_values("year")
        first = sub.iloc[0]
        last = sub.iloc[-1]
        span = int(last["year"] - first["year"])
        cagr_pct = None
        if span > 0 and first["sales_yi"] > 0 and last["sales_yi"] > 0:
            cagr_pct = ((last["sales_yi"] / first["sales_yi"]) ** (1 / span) - 1) * 100
        rows.append(
            {
                "股票代码": ts_code,
                "企业": name,
                "CAGR区间": f"{int(first['year'])}-{int(last['year'])}",
                "期初收入(亿元)": first["sales_yi"],
                "期末收入(亿元)": last["sales_yi"],
                "年数": span,
                "CAGR": cagr_pct,
            }
        )
    return pd.DataFrame(rows).sort_values(["股票代码"])


def format_number(value, pct: bool = False) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2f}%" if pct else f"{value:.2f}"


def print_tables(df: pd.DataFrame, keyword: str):
    latest_sales_map = (
        df.sort_values(["ts_code", "year"])
        .groupby("ts_code", as_index=False)
        .tail(1)[["ts_code", "sales_yi"]]
        .rename(columns={"sales_yi": "latest_sales_yi"})
    )
    detail_source = (
        df.merge(latest_sales_map, on="ts_code", how="left")
        .sort_values(["latest_sales_yi", "ts_code", "year"], ascending=[False, True, True])
    )

    detail_rows = []
    for _, row in detail_source.iterrows():
        detail_rows.append(
            {
                "股票代码": row["ts_code"],
                "企业": row["name"],
                "年份": int(row["year"]),
                "产品项": row["bz_item"],
                "收入(亿元)": format_number(row["sales_yi"]),
                "收入同比": format_number(row["yoy_pct"], pct=True),
                "利润(亿元)": format_number(row["profit_yi"]),
                "成本(亿元)": format_number(row["cost_yi"]),
                "毛利率": format_number(row["gross_margin_pct"], pct=True),
            }
        )
    detail_df = pd.DataFrame(detail_rows)

    summary_df = build_cagr_summary(df).copy()
    summary_df["期初收入(亿元)"] = summary_df["期初收入(亿元)"].map(format_number)
    summary_df["期末收入(亿元)"] = summary_df["期末收入(亿元)"].map(format_number)
    summary_df["CAGR"] = summary_df["CAGR"].map(lambda x: format_number(x, pct=True))

    print(f"\n## {keyword} 近五年主营业务明细\n")
    print(detail_df.to_markdown(index=False))
    print(f"\n## {keyword} CAGR 汇总\n")
    print(summary_df.to_markdown(index=False))


def main():
    parser = argparse.ArgumentParser(description="按产品关键字查询主营业务近五年数据")
    parser.add_argument("--keyword", required=True, help="产品关键字，例如：储能系统、光伏逆变器")
    args = parser.parse_args()

    engine = get_engine()
    raw_df = query_main_business(engine, args.keyword)
    if raw_df.empty:
        print(f"未查询到产品项包含“{args.keyword}”的近五个年度报告期数据。")
        return

    merged_df = merge_company_year_rows(raw_df)
    print_tables(merged_df, args.keyword)


if __name__ == "__main__":
    main()
