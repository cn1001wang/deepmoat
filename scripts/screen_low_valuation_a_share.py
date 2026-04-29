"""
作用：
从本地数据库筛选低估值 A 股候选池，重点关注较高 ROE、较大市值和估值偏低的股票，
结果会输出到 `outputs/` 供后续人工复盘或二次筛选。
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"


def load_engine():
    load_dotenv(dotenv_path=ROOT / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
    )
    db_url = database_url.replace("+psycopg2", "")
    return create_engine(db_url)


def fetch_daily_range(engine):
    sql = text("SELECT MIN(trade_date) AS min_trade_date, MAX(trade_date) AS max_trade_date FROM daily_basic")
    row = pd.read_sql(sql, engine).iloc[0]
    return str(row["min_trade_date"]), str(row["max_trade_date"])


def build_sql():
    return text(
        """
WITH latest_daily AS (
    SELECT
        db.ts_code,
        db.trade_date,
        db.pe_ttm,
        db.pb,
        db.total_mv,
        ROW_NUMBER() OVER (PARTITION BY db.ts_code ORDER BY db.trade_date DESC) AS rn
    FROM daily_basic db
),
latest_daily_one AS (
    SELECT ts_code, trade_date, pe_ttm, pb, total_mv
    FROM latest_daily
    WHERE rn = 1
),
latest_indicator AS (
    SELECT
        fi.ts_code,
        fi.end_date,
        fi.roe,
        fi.roe_yearly,
        ROW_NUMBER() OVER (PARTITION BY fi.ts_code ORDER BY fi.end_date DESC, fi.ann_date DESC) AS rn
    FROM fina_indicator fi
),
latest_income AS (
    SELECT
        i.ts_code,
        i.end_date,
        i.total_revenue,
        i.n_income_attr_p,
        ROW_NUMBER() OVER (PARTITION BY i.ts_code ORDER BY i.end_date DESC) AS rn
    FROM income i
),
latest_balance AS (
    SELECT
        b.ts_code,
        b.end_date,
        b.total_assets,
        b.total_liab,
        ROW_NUMBER() OVER (PARTITION BY b.ts_code ORDER BY b.end_date DESC) AS rn
    FROM balancesheet b
),
latest_cash AS (
    SELECT
        c.ts_code,
        c.end_date,
        c.n_cashflow_act,
        ROW_NUMBER() OVER (PARTITION BY c.ts_code ORDER BY c.end_date DESC) AS rn
    FROM cashflow c
),
hist_stats AS (
    SELECT
        ld.ts_code,
        SUM(CASE WHEN h.pe_ttm > 0 THEN 1 ELSE 0 END) AS pe_hist_n,
        SUM(CASE WHEN h.pb > 0 THEN 1 ELSE 0 END) AS pb_hist_n,
        SUM(CASE WHEN h.pe_ttm > 0 AND h.pe_ttm <= ld.pe_ttm THEN 1 ELSE 0 END) AS pe_le_cnt,
        SUM(CASE WHEN h.pb > 0 AND h.pb <= ld.pb THEN 1 ELSE 0 END) AS pb_le_cnt
    FROM latest_daily_one ld
    LEFT JOIN daily_basic h
        ON h.ts_code = ld.ts_code
       AND h.trade_date >= :hist_start
    GROUP BY ld.ts_code
)
SELECT
    sb.ts_code,
    sb.name,
    sb.industry,
    sb.list_date,
    ld.trade_date,
    ld.total_mv,
    ld.pe_ttm,
    ld.pb,
    li.end_date AS fina_end_date,
    COALESCE(li.roe_yearly, li.roe) AS roe_used,
    li.roe,
    li.roe_yearly,
    hs.pe_hist_n,
    hs.pb_hist_n,
    CASE
        WHEN hs.pe_hist_n > 0 AND ld.pe_ttm > 0 THEN hs.pe_le_cnt::float / hs.pe_hist_n
        ELSE NULL
    END AS pe_percentile_5y,
    CASE
        WHEN hs.pb_hist_n > 0 AND ld.pb > 0 THEN hs.pb_le_cnt::float / hs.pb_hist_n
        ELSE NULL
    END AS pb_percentile_5y,
    inc.total_revenue,
    inc.n_income_attr_p,
    bal.total_assets,
    bal.total_liab,
    c.n_cashflow_act
FROM stock_basic sb
JOIN latest_daily_one ld
    ON sb.ts_code = ld.ts_code
LEFT JOIN latest_indicator li
    ON sb.ts_code = li.ts_code AND li.rn = 1
LEFT JOIN hist_stats hs
    ON sb.ts_code = hs.ts_code
LEFT JOIN latest_income inc
    ON sb.ts_code = inc.ts_code AND inc.rn = 1
LEFT JOIN latest_balance bal
    ON sb.ts_code = bal.ts_code AND bal.rn = 1
LEFT JOIN latest_cash c
    ON sb.ts_code = c.ts_code AND c.rn = 1
WHERE sb.list_status = 'L'
  AND COALESCE(li.roe_yearly, li.roe) > :roe_min
  AND ld.total_mv >= :mv_min_wanyuan
  AND (
      (hs.pe_hist_n >= :min_hist_n AND ld.pe_ttm > 0 AND hs.pe_le_cnt::float / hs.pe_hist_n <= :low_q)
      OR
      (hs.pb_hist_n >= :min_hist_n AND ld.pb > 0 AND hs.pb_le_cnt::float / hs.pb_hist_n <= :low_q)
  )
ORDER BY
    LEAST(
        COALESCE(CASE WHEN hs.pe_hist_n > 0 AND ld.pe_ttm > 0 THEN hs.pe_le_cnt::float / hs.pe_hist_n END, 1.0),
        COALESCE(CASE WHEN hs.pb_hist_n > 0 AND ld.pb > 0 THEN hs.pb_le_cnt::float / hs.pb_hist_n END, 1.0)
    ) ASC,
    COALESCE(li.roe_yearly, li.roe) DESC
        """
    )


def enrich_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["market_cap_yi"] = out["total_mv"] / 10000.0
    out["debt_asset_ratio_pct"] = (out["total_liab"] / out["total_assets"]) * 100.0
    out["net_margin_pct"] = (out["n_income_attr_p"] / out["total_revenue"]) * 100.0
    out["roa_est_pct"] = (out["n_income_attr_p"] / out["total_assets"]) * 100.0
    out["ocf_to_profit"] = out["n_cashflow_act"] / out["n_income_attr_p"]
    out["value_score"] = out[["pe_percentile_5y", "pb_percentile_5y"]].min(axis=1, skipna=True)
    out["valuation_low_by"] = out.apply(
        lambda r: "PE&PB"
        if pd.notna(r["pe_percentile_5y"]) and pd.notna(r["pb_percentile_5y"]) and r["pe_percentile_5y"] <= 0.30 and r["pb_percentile_5y"] <= 0.30
        else ("PE" if pd.notna(r["pe_percentile_5y"]) and r["pe_percentile_5y"] <= 0.30 else "PB"),
        axis=1,
    )
    return out


def add_growth_metrics(engine, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    codes = df["ts_code"].dropna().astype(str).tolist()
    params = {f"c{i}": code for i, code in enumerate(codes)}
    placeholders = ", ".join(f":c{i}" for i in range(len(codes)))

    sql = text(
        f"""
WITH annual_income AS (
    SELECT
        i.ts_code,
        i.end_date,
        i.total_revenue,
        i.n_income_attr_p,
        ROW_NUMBER() OVER (PARTITION BY i.ts_code ORDER BY i.end_date DESC) AS rn
    FROM income i
    WHERE i.end_date LIKE '%1231'
      AND i.ts_code IN ({placeholders})
),
p AS (
    SELECT
        a1.ts_code,
        a1.end_date AS latest_annual_end,
        a1.total_revenue AS latest_revenue,
        a2.total_revenue AS prev_revenue,
        a1.n_income_attr_p AS latest_profit,
        a2.n_income_attr_p AS prev_profit
    FROM annual_income a1
    LEFT JOIN annual_income a2
      ON a1.ts_code = a2.ts_code AND a2.rn = 2
    WHERE a1.rn = 1
)
SELECT
    ts_code,
    latest_annual_end,
    CASE
        WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN NULL
        ELSE (latest_revenue - prev_revenue) / ABS(prev_revenue) * 100
    END AS revenue_yoy_pct,
    CASE
        WHEN prev_profit IS NULL OR prev_profit = 0 THEN NULL
        ELSE (latest_profit - prev_profit) / ABS(prev_profit) * 100
    END AS profit_yoy_pct
FROM p
        """
    )
    growth_df = pd.read_sql(sql, engine, params=params)
    return df.merge(growth_df, on="ts_code", how="left")


def save_outputs(df: pd.DataFrame):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    csv_path = OUTPUT_DIR / f"screen-roe12-mv100-low-valuation-{today}.csv"
    json_path = OUTPUT_DIR / f"screen-roe12-mv100-low-valuation-{today}.json"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(
        json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return csv_path, json_path


def main():
    engine = load_engine()
    min_trade_date, max_trade_date = fetch_daily_range(engine)
    requested_hist_start = (date.today() - timedelta(days=365 * 5)).strftime("%Y%m%d")
    hist_start = max(requested_hist_start, min_trade_date)
    sql = build_sql()
    params = {
        "hist_start": hist_start,
        "roe_min": 12.0,
        "mv_min_wanyuan": 1_000_000.0,  # 100亿 = 1,000,000 万元
        "min_hist_n": 20,
        "low_q": 0.30,
    }
    df = pd.read_sql(sql, engine, params=params)
    if df.empty:
        print("No candidates found.")
        print(f"History window used: {hist_start} ~ {max_trade_date}")
        return

    df = enrich_metrics(df)
    df = add_growth_metrics(engine, df)
    df = df.sort_values(["value_score", "roe_used"], ascending=[True, False]).reset_index(drop=True)
    csv_path, json_path = save_outputs(df)

    print(f"History window used: {hist_start} ~ {max_trade_date}")
    print(f"Total candidates: {len(df)}")
    print(f"Top 20:\n{df[['ts_code', 'name', 'industry', 'trade_date', 'roe_used', 'market_cap_yi', 'pe_ttm', 'pb', 'pe_percentile_5y', 'pb_percentile_5y']].head(20).to_string(index=False)}")
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")


if __name__ == "__main__":
    main()
