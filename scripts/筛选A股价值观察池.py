"""
作用：
基于本地 PostgreSQL 财务库，对 A 股做“先排雷、再筛财务质量、再评估成长与现金流”的
价值观察池筛选，并输出可复盘的 CSV / JSON / Markdown 结果。

适用场景：
1. 需要从全市场快速过滤出值得进一步研究的公司；
2. 需要按稳健价值、高质量成长、高股息低估值、困境反转四类观察池分类；
3. 需要明确数据口径、排除原因、风险标记和 100 分制评分。
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
DEFAULT_DB_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/testdb"
EXEMPT_INDUSTRY_KEYWORDS = ("银行", "证券", "保险", "多元金融", "房地产", "电力", "燃气", "水务", "公用")


@dataclass
class ScreenConfig:
    stable_roe_min: float = 10.0
    stable_positive_profit_years_min: int = 4
    stable_ocf_profit_min: float = 0.8
    stable_positive_ocf_years_min: int = 4
    stable_debt_ratio_max: float = 60.0
    stable_goodwill_ratio_max: float = 20.0
    stable_dividend_yield_min: float = 2.0
    stable_fcf_yield_min: float = 5.0

    growth_roe_min: float = 15.0
    growth_revenue_cagr_min: float = 8.0
    growth_profit_cagr_min: float = 8.0
    growth_ocf_profit_min: float = 0.8
    growth_debt_ratio_max: float = 60.0

    dividend_yield_min: float = 3.0
    dividend_years_min: int = 5
    dividend_payout_mean_min: float = 15.0
    dividend_payout_mean_max: float = 80.0
    dividend_ocf_cover_min: float = 1.0
    dividend_positive_ocf_years_min: int = 4

    turnaround_valuation_percentile_max: float = 60.0
    turnaround_ocf_profit_min: float = 0.6
    turnaround_debt_ratio_max: float = 65.0

    top_per_category: int = 15
    overall_top_n: int = 40

    exclude_goodwill_ratio_max: float = 30.0
    exclude_debt_ratio_max: float = 70.0
    exclude_pledge_ratio_warn: float = 30.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="筛选 A 股价值投资观察池")

    parser.add_argument(
        "--output-prefix",
        default="a_share_watchlist",
        help="输出文件名前缀，会自动拼接数据日期",
    )
    parser.add_argument("--top-per-category", type=int, default=15, help="每个观察池输出前 N 家")
    parser.add_argument("--overall-top-n", type=int, default=40, help="综合观察池输出前 N 家")

    parser.add_argument("--stable-roe-min", type=float, default=10.0)
    parser.add_argument("--stable-positive-profit-years-min", type=int, default=4)
    parser.add_argument("--stable-ocf-profit-min", type=float, default=0.8)
    parser.add_argument("--stable-positive-ocf-years-min", type=int, default=4)
    parser.add_argument("--stable-debt-ratio-max", type=float, default=60.0)
    parser.add_argument("--stable-goodwill-ratio-max", type=float, default=20.0)
    parser.add_argument("--stable-dividend-yield-min", type=float, default=2.0)
    parser.add_argument("--stable-fcf-yield-min", type=float, default=5.0)

    parser.add_argument("--growth-roe-min", type=float, default=15.0)
    parser.add_argument("--growth-revenue-cagr-min", type=float, default=8.0)
    parser.add_argument("--growth-profit-cagr-min", type=float, default=8.0)
    parser.add_argument("--growth-ocf-profit-min", type=float, default=0.8)
    parser.add_argument("--growth-debt-ratio-max", type=float, default=60.0)

    parser.add_argument("--dividend-yield-min", type=float, default=3.0)
    parser.add_argument("--dividend-years-min", type=int, default=5)
    parser.add_argument("--dividend-payout-mean-min", type=float, default=15.0)
    parser.add_argument("--dividend-payout-mean-max", type=float, default=80.0)
    parser.add_argument("--dividend-ocf-cover-min", type=float, default=1.0)
    parser.add_argument("--dividend-positive-ocf-years-min", type=int, default=4)

    parser.add_argument("--turnaround-valuation-percentile-max", type=float, default=60.0)
    parser.add_argument("--turnaround-ocf-profit-min", type=float, default=0.6)
    parser.add_argument("--turnaround-debt-ratio-max", type=float, default=65.0)

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ScreenConfig:
    return ScreenConfig(
        stable_roe_min=args.stable_roe_min,
        stable_positive_profit_years_min=args.stable_positive_profit_years_min,
        stable_ocf_profit_min=args.stable_ocf_profit_min,
        stable_positive_ocf_years_min=args.stable_positive_ocf_years_min,
        stable_debt_ratio_max=args.stable_debt_ratio_max,
        stable_goodwill_ratio_max=args.stable_goodwill_ratio_max,
        stable_dividend_yield_min=args.stable_dividend_yield_min,
        stable_fcf_yield_min=args.stable_fcf_yield_min,
        growth_roe_min=args.growth_roe_min,
        growth_revenue_cagr_min=args.growth_revenue_cagr_min,
        growth_profit_cagr_min=args.growth_profit_cagr_min,
        growth_ocf_profit_min=args.growth_ocf_profit_min,
        growth_debt_ratio_max=args.growth_debt_ratio_max,
        dividend_yield_min=args.dividend_yield_min,
        dividend_years_min=args.dividend_years_min,
        dividend_payout_mean_min=args.dividend_payout_mean_min,
        dividend_payout_mean_max=args.dividend_payout_mean_max,
        dividend_ocf_cover_min=args.dividend_ocf_cover_min,
        dividend_positive_ocf_years_min=args.dividend_positive_ocf_years_min,
        turnaround_valuation_percentile_max=args.turnaround_valuation_percentile_max,
        turnaround_ocf_profit_min=args.turnaround_ocf_profit_min,
        turnaround_debt_ratio_max=args.turnaround_debt_ratio_max,
        top_per_category=args.top_per_category,
        overall_top_n=args.overall_top_n,
    )


def load_engine():
    load_dotenv(ROOT / ".env")
    db_url = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    return create_engine(db_url)


def clamp(value: float | None, low: float, high: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return max(low, min(high, float(value)))


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if pd.isna(numerator) or pd.isna(denominator) or float(denominator) == 0:
        return None
    return float(numerator) / float(denominator)


def pct(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100.0


def to_yi(value: float | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value) / 1e8


def cagr(series: list[float | None]) -> float | None:
    clean = [float(v) for v in series if v is not None and not pd.isna(v)]
    if len(clean) < 2:
        return None
    start = clean[-1]
    end = clean[0]
    periods = len(clean) - 1
    if start <= 0 or end <= 0 or periods <= 0:
        return None
    return (pow(end / start, 1 / periods) - 1) * 100.0


def avg(values: list[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and not pd.isna(v)]
    if not clean:
        return None
    return sum(clean) / len(clean)


def median(values: list[float | None]) -> float | None:
    clean = sorted(float(v) for v in values if v is not None and not pd.isna(v))
    if not clean:
        return None
    return float(pd.Series(clean).median())


def is_non_standard_audit(audit_result: str | None) -> bool:
    if audit_result is None or pd.isna(audit_result):
        return False
    audit_result = str(audit_result)
    if not audit_result:
        return False
    if any(flag in audit_result for flag in ("否定意见", "无法表示意见", "拒绝表示意见")):
        return True
    return "保留意见" in audit_result and "无保留意见" not in audit_result


def is_exempt_industry(industry: str | None) -> bool:
    if industry is None or pd.isna(industry):
        return False
    industry = str(industry)
    if not industry:
        return False
    return any(keyword in industry for keyword in EXEMPT_INDUSTRY_KEYWORDS)


def latest_distinct_query(table: str, fields: str, where_clause: str = "") -> str:
    where_sql = f"WHERE {where_clause}" if where_clause else ""
    return f"""
    SELECT DISTINCT ON (ts_code) {fields}
    FROM {table}
    {where_sql}
    ORDER BY ts_code, end_date DESC, ann_date DESC
    """


def load_base_frames(engine) -> dict[str, pd.DataFrame]:
    sqls = {
        "stocks": """
            SELECT ts_code, name, industry, area, market, list_date, list_status
            FROM stock_basic
            WHERE list_status = 'L'
        """,
        "daily_latest": """
            SELECT DISTINCT ON (ts_code)
                ts_code, trade_date, close, pe_ttm, pb, ps_ttm, dv_ttm, total_mv, total_share
            FROM daily_basic
            ORDER BY ts_code, trade_date DESC
        """,
        "daily_hist": """
            SELECT ts_code, trade_date, pe_ttm, pb
            FROM daily_basic
            ORDER BY ts_code, trade_date DESC
        """,
        "indicator_annual": """
            SELECT DISTINCT ON (ts_code, end_date)
                ts_code, ann_date, end_date,
                profit_dedt, grossprofit_margin, netprofit_margin,
                roe, roe_yearly, roic, roic_yearly,
                debt_to_assets, ocf_to_profit, or_yoy, dt_netprofit_yoy
            FROM fina_indicator
            WHERE end_date LIKE '%1231'
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
        "indicator_latest": latest_distinct_query(
            "fina_indicator",
            "ts_code, ann_date, end_date, grossprofit_margin, netprofit_margin, roic, roic_yearly, "
            "roe, roe_yearly, debt_to_assets, ocf_to_profit, or_yoy, dt_netprofit_yoy, q_dtprofit, q_sales_yoy"
        ),
        "income_annual": """
            SELECT DISTINCT ON (ts_code, end_date)
                ts_code, ann_date, end_date, total_revenue, n_income_attr_p
            FROM income
            WHERE end_date LIKE '%1231'
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
        "balance_annual": """
            SELECT DISTINCT ON (ts_code, end_date)
                ts_code, ann_date, end_date,
                total_assets, total_liab, money_cap, st_borr, lt_borr, nca_within_1y,
                bond_payable, goodwill, total_hldr_eqy_exc_min_int,
                accounts_receiv, inventories
            FROM balancesheet
            WHERE end_date LIKE '%1231'
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
        "balance_latest": latest_distinct_query(
            "balancesheet",
            "ts_code, ann_date, end_date, total_assets, total_liab, money_cap, st_borr, lt_borr, "
            "nca_within_1y, bond_payable, goodwill, total_hldr_eqy_exc_min_int, accounts_receiv, inventories"
        ),
        "cashflow_annual": """
            SELECT DISTINCT ON (ts_code, end_date)
                ts_code, ann_date, end_date,
                n_cashflow_act, n_cashflow_inv_act, n_cash_flows_fnc_act,
                free_cashflow, c_pay_acq_const_fiolta
            FROM cashflow
            WHERE end_date LIKE '%1231'
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
        "cashflow_latest": latest_distinct_query(
            "cashflow",
            "ts_code, ann_date, end_date, n_cashflow_act, free_cashflow, n_cashflow_inv_act, n_cash_flows_fnc_act"
        ),
        "audit_latest": """
            SELECT DISTINCT ON (ts_code) ts_code, end_date, ann_date, audit_result, audit_agency
            FROM fina_audit
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
        "dividend": """
            SELECT ts_code, end_date, ann_date, div_proc, cash_div_tax, base_share
            FROM dividend
            WHERE div_proc = '实施'
            ORDER BY ts_code, end_date DESC, ann_date DESC
        """,
    }
    return {name: pd.read_sql(text(sql), engine) for name, sql in sqls.items()}


def build_daily_hist_metrics(daily_hist: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ts_code, group in daily_hist.groupby("ts_code", sort=False):
        pe_series = group["pe_ttm"].dropna()
        pe_series = pe_series[pe_series > 0]
        pb_series = group["pb"].dropna()
        pb_series = pb_series[pb_series > 0]

        latest_pe = float(pe_series.iloc[0]) if not pe_series.empty else None
        latest_pb = float(pb_series.iloc[0]) if not pb_series.empty else None

        pe_percentile = float(pe_series.le(latest_pe).mean() * 100.0) if latest_pe is not None and not pe_series.empty else None
        pb_percentile = float(pb_series.le(latest_pb).mean() * 100.0) if latest_pb is not None and not pb_series.empty else None

        rows.append(
            {
                "ts_code": ts_code,
                "valuation_trade_days": int(group["trade_date"].nunique()),
                "valuation_window_start": group["trade_date"].min(),
                "valuation_window_end": group["trade_date"].max(),
                "pe_median_window": float(pe_series.median()) if not pe_series.empty else None,
                "pb_median_window": float(pb_series.median()) if not pb_series.empty else None,
                "pe_percentile_window": pe_percentile,
                "pb_percentile_window": pb_percentile,
            }
        )
    return pd.DataFrame(rows)


def implemented_dividend_totals(dividend_df: pd.DataFrame) -> pd.DataFrame:
    if dividend_df.empty:
        return pd.DataFrame(columns=["ts_code", "end_date", "dividend_total"])
    df = dividend_df.copy()
    df["dividend_total"] = df.apply(
        lambda row: float(row["cash_div_tax"]) * float(row["base_share"]) * 10000
        if pd.notna(row["cash_div_tax"]) and pd.notna(row["base_share"])
        else None,
        axis=1,
    )
    df = df.dropna(subset=["dividend_total"])
    df = df.sort_values(["ts_code", "end_date", "ann_date"], ascending=[True, False, False])
    df = df.drop_duplicates(subset=["ts_code", "end_date"], keep="first")
    return df[["ts_code", "end_date", "dividend_total"]]


def latest_value(df: pd.DataFrame, col: str) -> float | None:
    if df.empty or col not in df:
        return None
    value = df.iloc[0][col]
    return None if pd.isna(value) else float(value)


def series_values(df: pd.DataFrame, col: str, limit: int = 5) -> list[float | None]:
    if df.empty or col not in df:
        return []
    values: list[float | None] = []
    for value in df[col].head(limit).tolist():
        values.append(None if pd.isna(value) else float(value))
    return values


def yoy_growth_series(values: list[float | None]) -> list[float | None]:
    out: list[float | None] = []
    for newer, older in zip(values, values[1:]):
        if newer is None or older is None or older == 0:
            out.append(None)
        else:
            out.append((newer - older) / abs(older) * 100.0)
    return out


def bool_text(flag: bool) -> str:
    return "是" if flag else "否"


def score_range(value: float | None, floor: float, ceiling: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if ceiling == floor:
        return 0.0
    return clamp((float(value) - floor) / (ceiling - floor), 0.0, 1.0)


def inverse_score(value: float | None, good: float, bad: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if bad == good:
        return 0.0
    return clamp((bad - float(value)) / (bad - good), 0.0, 1.0)


def build_company_metrics(frames: dict[str, pd.DataFrame], config: ScreenConfig) -> pd.DataFrame:
    stocks = frames["stocks"].copy()
    indicator_latest = frames["indicator_latest"].rename(
        columns={
            "ann_date": "indicator_ann_date",
            "end_date": "indicator_end_date",
        }
    )
    balance_latest = frames["balance_latest"].rename(
        columns={
            "ann_date": "balance_ann_date",
            "end_date": "balance_end_date",
        }
    )
    cashflow_latest = frames["cashflow_latest"].rename(
        columns={
            "ann_date": "cash_ann_date",
            "end_date": "cash_end_date",
        }
    )
    audit_latest = frames["audit_latest"].rename(
        columns={
            "ann_date": "audit_latest_ann_date",
            "end_date": "audit_latest_end_date",
        }
    )

    base = stocks.merge(frames["daily_latest"], on="ts_code", how="left")
    base = base.merge(build_daily_hist_metrics(frames["daily_hist"]), on="ts_code", how="left")
    base = base.merge(indicator_latest, on="ts_code", how="left")
    base = base.merge(balance_latest, on="ts_code", how="left")
    base = base.merge(cashflow_latest, on="ts_code", how="left")
    base = base.merge(audit_latest, on="ts_code", how="left")

    annual_indicator = frames["indicator_annual"].sort_values(["ts_code", "end_date"], ascending=[True, False])
    annual_income = frames["income_annual"].sort_values(["ts_code", "end_date"], ascending=[True, False])
    annual_balance = frames["balance_annual"].sort_values(["ts_code", "end_date"], ascending=[True, False])
    annual_cash = frames["cashflow_annual"].sort_values(["ts_code", "end_date"], ascending=[True, False])
    dividends = implemented_dividend_totals(frames["dividend"])

    industry_roic = (
        frames["indicator_latest"]
        .merge(stocks[["ts_code", "industry"]], on="ts_code", how="left")
        .assign(roic_used=lambda df: df["roic_yearly"].fillna(df["roic"]))
        .groupby("industry", dropna=False)["roic_used"]
        .mean()
        .rename("industry_roic_avg")
        .reset_index()
    )
    base = base.merge(industry_roic, on="industry", how="left")

    annual_indicator_groups = {code: df.head(5).copy() for code, df in annual_indicator.groupby("ts_code")}
    annual_income_groups = {code: df.head(5).copy() for code, df in annual_income.groupby("ts_code")}
    annual_balance_groups = {code: df.head(5).copy() for code, df in annual_balance.groupby("ts_code")}
    annual_cash_groups = {code: df.head(5).copy() for code, df in annual_cash.groupby("ts_code")}
    dividend_groups = {code: df.head(5).copy() for code, df in dividends.groupby("ts_code")}

    records: list[dict[str, Any]] = []
    for row in base.to_dict(orient="records"):
        code = row["ts_code"]
        ind_df = annual_indicator_groups.get(code, pd.DataFrame())
        inc_df = annual_income_groups.get(code, pd.DataFrame())
        bal_df = annual_balance_groups.get(code, pd.DataFrame())
        cash_df = annual_cash_groups.get(code, pd.DataFrame())
        div_df = dividend_groups.get(code, pd.DataFrame())

        roe_values = series_values(ind_df, "roe_yearly")
        if not any(v is not None for v in roe_values):
            roe_values = series_values(ind_df, "roe")
        roic_values = series_values(ind_df, "roic_yearly")
        if not any(v is not None for v in roic_values):
            roic_values = series_values(ind_df, "roic")
        gm_values = series_values(ind_df, "grossprofit_margin")
        nm_values = series_values(ind_df, "netprofit_margin")
        dt_profit_values = series_values(ind_df, "profit_dedt")
        revenue_values = series_values(inc_df, "total_revenue")
        net_income_values = series_values(inc_df, "n_income_attr_p")
        ocf_values = series_values(cash_df, "n_cashflow_act")
        fcf_values = series_values(cash_df, "free_cashflow")
        financing_values = series_values(cash_df, "n_cash_flows_fnc_act")
        ar_values = series_values(bal_df, "accounts_receiv")
        inv_values = series_values(bal_df, "inventories")

        debt_ratio = pct(safe_div(row.get("total_liab"), row.get("total_assets")))
        equity = row.get("total_hldr_eqy_exc_min_int")
        goodwill_ratio = pct(safe_div(row.get("goodwill"), equity))
        short_debt = sum(
            float(v)
            for v in [row.get("st_borr"), row.get("nca_within_1y")]
            if v is not None and not pd.isna(v)
        )
        interest_debt = sum(
            float(v)
            for v in [row.get("st_borr"), row.get("lt_borr"), row.get("nca_within_1y"), row.get("bond_payable")]
            if v is not None and not pd.isna(v)
        )
        cash_cover_short_debt = safe_div(row.get("money_cap"), short_debt if short_debt else None)
        interest_debt_to_equity = safe_div(interest_debt, equity)

        dt_profit_positive_years = sum(1 for v in dt_profit_values if v is not None and v > 0)
        ocf_positive_years = sum(1 for v in ocf_values if v is not None and v > 0)
        fcf_positive_years = sum(1 for v in fcf_values if v is not None and v > 0)
        ocf_5y = sum(v for v in ocf_values if v is not None)
        net_income_5y = sum(v for v in net_income_values if v is not None)
        dt_profit_5y = sum(v for v in dt_profit_values if v is not None)
        fcf_5y = sum(v for v in fcf_values if v is not None)
        dividend_5y = float(div_df["dividend_total"].sum()) if not div_df.empty else 0.0
        ocf_profit_ratio_5y = safe_div(ocf_5y, net_income_5y)
        ocf_dt_profit_ratio_5y = safe_div(ocf_5y, dt_profit_5y)
        dividend_ocf_cover = safe_div(ocf_5y, dividend_5y if dividend_5y > 0 else None)
        dividend_payout_mean = None
        if not div_df.empty and not inc_df.empty:
            merged_div = inc_df[["end_date", "n_income_attr_p"]].merge(div_df, on="end_date", how="left")
            payout_list = [
                pct(safe_div(div_total, profit))
                for div_total, profit in zip(merged_div["dividend_total"], merged_div["n_income_attr_p"])
                if pd.notna(div_total) and pd.notna(profit) and float(profit) > 0
            ]
            dividend_payout_mean = avg(payout_list)

        revenue_cagr_5y = cagr(revenue_values)
        dt_profit_cagr_5y = cagr(dt_profit_values)
        roe_avg_5y = avg(roe_values)
        roic_avg_5y = avg(roic_values)
        gross_margin_avg_5y = avg(gm_values)
        net_margin_avg_5y = avg(nm_values)

        revenue_yoy = yoy_growth_series(revenue_values[:3])
        ar_yoy = yoy_growth_series(ar_values[:3])
        inv_yoy = yoy_growth_series(inv_values[:3])
        ar_risk_flag = len(revenue_yoy) >= 2 and len(ar_yoy) >= 2 and all(
            rv is not None and av is not None and av > rv
            for av, rv in zip(ar_yoy[:2], revenue_yoy[:2])
        )
        inv_risk_flag = len(revenue_yoy) >= 2 and len(inv_yoy) >= 2 and all(
            rv is not None and iv is not None and iv > rv
            for iv, rv in zip(inv_yoy[:2], revenue_yoy[:2])
        )

        latest_roic = row.get("roic_yearly")
        if pd.isna(latest_roic):
            latest_roic = row.get("roic")
        latest_roe = row.get("roe_yearly")
        if pd.isna(latest_roe):
            latest_roe = row.get("roe")

        latest_gm = row.get("grossprofit_margin")
        latest_nm = row.get("netprofit_margin")
        prev_gm = gm_values[1] if len(gm_values) > 1 else None
        prev_nm = nm_values[1] if len(nm_values) > 1 else None
        margin_repair = (
            (latest_gm is not None and prev_gm is not None and latest_gm >= prev_gm)
            or (latest_nm is not None and prev_nm is not None and latest_nm >= prev_nm)
        )
        gross_margin_trend_ok = (
            latest_gm is not None
            and gross_margin_avg_5y is not None
            and latest_gm >= gross_margin_avg_5y - 1.0
        )

        low_profit_base = (
            bool(dt_profit_values)
            and median(dt_profit_values) is not None
            and dt_profit_values[0] is not None
            and dt_profit_values[0] <= median(dt_profit_values) * 0.9
        )
        valuation_window_ok = (row.get("valuation_trade_days") or 0) >= 20
        valuation_low_flag = valuation_window_ok and (
            (row.get("pe_ttm") is not None and row.get("pe_median_window") is not None and row["pe_ttm"] <= row["pe_median_window"])
            or (row.get("pb") is not None and row.get("pb_median_window") is not None and row["pb"] <= row["pb_median_window"])
        )
        turnaround_evidence = [
            label
            for ok, label in [
                (low_profit_base, "利润仍处于近年偏低区间"),
                (margin_repair, "毛利率或净利率出现修复"),
                (
                    row.get("ocf_to_profit") is not None and row["ocf_to_profit"] >= config.turnaround_ocf_profit_min,
                    "经营现金流未明显恶化",
                ),
                (valuation_low_flag, "估值仍处于可接受的偏低位置"),
            ]
            if ok
        ]
        turnaround_risks = [
            label
            for ok, label in [
                (ar_risk_flag, "应收账款增速连续高于营收"),
                (inv_risk_flag, "存货增速连续高于营收"),
                (goodwill_ratio is not None and goodwill_ratio > 20.0, "商誉占净资产偏高"),
                (debt_ratio is not None and debt_ratio > 60.0 and not is_exempt_industry(row.get("industry")), "负债率偏高"),
            ]
            if ok
        ]

        pe_low_pct = row.get("pe_percentile_window")
        pb_low_pct = row.get("pb_percentile_window")
        dv_ttm = row.get("dv_ttm")
        total_mv_yuan = float(row["total_mv"]) * 10000 if row.get("total_mv") is not None and not pd.isna(row.get("total_mv")) else None
        fcf_yield = pct(safe_div(latest_value(cash_df, "free_cashflow"), total_mv_yuan))

        exclude_reasons: list[str] = []
        risk_flags: list[str] = []

        name = str(row.get("name") or "")
        if name.startswith("ST") or name.startswith("*ST") or "ST" in name:
            exclude_reasons.append("ST/*ST/风险警示")
        if is_non_standard_audit(row.get("audit_result")):
            exclude_reasons.append("最近一期审计意见非标准无保留")
        if len(dt_profit_values) >= 3 and all(v is not None and v < 0 for v in dt_profit_values[:3]):
            exclude_reasons.append("最近3年扣非净利润连续为负")
        if len(ocf_values) >= 5 and ocf_5y < 0:
            exclude_reasons.append("最近5年经营现金流累计为负")
        if goodwill_ratio is not None and goodwill_ratio > config.exclude_goodwill_ratio_max:
            exclude_reasons.append(f"商誉/净资产 {goodwill_ratio:.1f}% > {config.exclude_goodwill_ratio_max:.0f}%")
        if (
            debt_ratio is not None
            and debt_ratio > config.exclude_debt_ratio_max
            and not is_exempt_industry(row.get("industry"))
        ):
            exclude_reasons.append(f"资产负债率 {debt_ratio:.1f}% > {config.exclude_debt_ratio_max:.0f}%")
        if ar_risk_flag:
            risk_flags.append("应收增速连续高于营收")
        if inv_risk_flag:
            risk_flags.append("存货增速连续高于营收")
        risk_flags.append("大股东质押比例：本地库缺失，需二次核验")

        stable_value_ok = (
            not exclude_reasons
            and roe_avg_5y is not None and roe_avg_5y > config.stable_roe_min
            and dt_profit_positive_years >= config.stable_positive_profit_years_min
            and ocf_dt_profit_ratio_5y is not None and ocf_dt_profit_ratio_5y > config.stable_ocf_profit_min
            and ocf_positive_years >= config.stable_positive_ocf_years_min
            and (
                debt_ratio is None
                or debt_ratio < config.stable_debt_ratio_max
                or is_exempt_industry(row.get("industry"))
            )
            and (goodwill_ratio is None or goodwill_ratio < config.stable_goodwill_ratio_max)
            and valuation_low_flag
            and (
                (dv_ttm is not None and dv_ttm > config.stable_dividend_yield_min)
                or (fcf_yield is not None and fcf_yield > config.stable_fcf_yield_min)
            )
        )

        high_quality_growth_ok = (
            not exclude_reasons
            and roe_avg_5y is not None and roe_avg_5y > config.growth_roe_min
            and revenue_cagr_5y is not None and revenue_cagr_5y > config.growth_revenue_cagr_min
            and dt_profit_cagr_5y is not None and dt_profit_cagr_5y > config.growth_profit_cagr_min
            and gross_margin_trend_ok
            and ocf_dt_profit_ratio_5y is not None and ocf_dt_profit_ratio_5y > config.growth_ocf_profit_min
            and debt_ratio is not None and debt_ratio < config.growth_debt_ratio_max
            and latest_roic is not None and row.get("industry_roic_avg") is not None and latest_roic > row["industry_roic_avg"]
        )

        high_dividend_ok = (
            not exclude_reasons
            and dv_ttm is not None and dv_ttm > config.dividend_yield_min
            and len(div_df) >= config.dividend_years_min
            and dividend_payout_mean is not None
            and config.dividend_payout_mean_min <= dividend_payout_mean <= config.dividend_payout_mean_max
            and dividend_ocf_cover is not None and dividend_ocf_cover >= config.dividend_ocf_cover_min
            and ocf_positive_years >= config.dividend_positive_ocf_years_min
            and valuation_low_flag
            and revenue_cagr_5y is not None and revenue_cagr_5y > -3.0
            and dt_profit_positive_years >= 4
        )

        turnaround_ok = (
            not exclude_reasons
            and low_profit_base
            and margin_repair
            and row.get("ocf_to_profit") is not None and row["ocf_to_profit"] >= config.turnaround_ocf_profit_min
            and (
                debt_ratio is None
                or debt_ratio <= config.turnaround_debt_ratio_max
                or is_exempt_industry(row.get("industry"))
            )
            and (
                (pe_low_pct is not None and pe_low_pct <= config.turnaround_valuation_percentile_max)
                or (pb_low_pct is not None and pb_low_pct <= config.turnaround_valuation_percentile_max)
            )
        )

        financial_score = (
            score_range(roe_avg_5y, 5.0, 20.0) * 7.0
            + score_range(roic_avg_5y, 5.0, 18.0) * 6.0
            + score_range(gross_margin_avg_5y, 15.0, 50.0) * 4.0
            + score_range(net_margin_avg_5y, 5.0, 25.0) * 4.0
            + clamp(dt_profit_positive_years / 5.0, 0.0, 1.0) * 4.0
        )
        cashflow_score = (
            clamp(ocf_positive_years / 5.0, 0.0, 1.0) * 7.0
            + score_range(ocf_dt_profit_ratio_5y, 0.5, 1.4) * 8.0
            + clamp(fcf_positive_years / 5.0, 0.0, 1.0) * 5.0
            + score_range(dividend_ocf_cover, 0.8, 2.5) * 5.0
        )
        balance_score = (
            inverse_score(debt_ratio, 30.0, 80.0) * 5.0
            + inverse_score(pct(interest_debt_to_equity), 10.0, 120.0) * 4.0
            + score_range(cash_cover_short_debt, 0.5, 2.0) * 4.0
            + inverse_score(goodwill_ratio, 0.0, 30.0) * 3.0
            + (4.0 - (2.0 if ar_risk_flag else 0.0) - (2.0 if inv_risk_flag else 0.0))
        )
        industry_proxy = avg([row.get("or_yoy"), row.get("dt_netprofit_yoy")])
        roic_vs_industry = safe_div(latest_roic, row.get("industry_roic_avg"))
        company_position_proxy = avg(
            [
                roic_vs_industry * 100 if roic_vs_industry is not None else None,
                latest_gm - gross_margin_avg_5y + 100 if latest_gm is not None and gross_margin_avg_5y is not None else None,
            ]
        )
        growth_score = (
            score_range(revenue_cagr_5y, 0.0, 20.0) * 4.0
            + score_range(dt_profit_cagr_5y, 0.0, 20.0) * 4.0
            + score_range(industry_proxy, -10.0, 20.0) * 3.0
            + score_range(company_position_proxy, 95.0, 125.0) * 4.0
        )
        valuation_score = (
            inverse_score(pe_low_pct, 10.0, 90.0) * 4.0
            + inverse_score(pb_low_pct, 10.0, 90.0) * 4.0
            + score_range(dv_ttm, 1.0, 5.0) * 3.0
            + score_range(fcf_yield, 1.0, 8.0) * 2.0
            + (2.0 if valuation_low_flag and not exclude_reasons else 0.0)
        )
        total_score = financial_score + cashflow_score + balance_score + growth_score + valuation_score
        total_score -= 2.0 if ar_risk_flag else 0.0
        total_score -= 2.0 if inv_risk_flag else 0.0

        records.append(
            {
                **row,
                "data_trade_date": row.get("trade_date"),
                "data_finance_end_date": row.get("indicator_end_date"),
                "debt_ratio_pct": debt_ratio,
                "goodwill_to_equity_pct": goodwill_ratio,
                "interest_debt_yi": to_yi(interest_debt),
                "short_debt_yi": to_yi(short_debt),
                "money_cap_yi": to_yi(row.get("money_cap")),
                "cash_cover_short_debt": cash_cover_short_debt,
                "interest_debt_to_equity_pct": pct(interest_debt_to_equity),
                "roe_avg_5y": roe_avg_5y,
                "roic_avg_5y": roic_avg_5y,
                "gross_margin_avg_5y": gross_margin_avg_5y,
                "net_margin_avg_5y": net_margin_avg_5y,
                "revenue_cagr_5y": revenue_cagr_5y,
                "dt_profit_cagr_5y": dt_profit_cagr_5y,
                "dt_profit_positive_years": dt_profit_positive_years,
                "ocf_positive_years": ocf_positive_years,
                "fcf_positive_years": fcf_positive_years,
                "ocf_5y_yi": to_yi(ocf_5y),
                "net_income_5y_yi": to_yi(net_income_5y),
                "dt_profit_5y_yi": to_yi(dt_profit_5y),
                "fcf_5y_yi": to_yi(fcf_5y),
                "ocf_net_income_ratio_5y": ocf_profit_ratio_5y,
                "ocf_dt_profit_ratio_5y": ocf_dt_profit_ratio_5y,
                "dividend_5y_yi": to_yi(dividend_5y),
                "dividend_years": int(len(div_df)),
                "dividend_payout_mean_pct": dividend_payout_mean,
                "dividend_ocf_cover": dividend_ocf_cover,
                "fcf_yield_pct": fcf_yield,
                "ar_risk_flag": ar_risk_flag,
                "inventory_risk_flag": inv_risk_flag,
                "exclude_reason_count": len(exclude_reasons),
                "exclude_reasons": "；".join(exclude_reasons),
                "risk_flags": "；".join(risk_flags),
                "stable_value_ok": stable_value_ok,
                "high_quality_growth_ok": high_quality_growth_ok,
                "high_dividend_ok": high_dividend_ok,
                "turnaround_ok": turnaround_ok,
                "turnaround_evidence": "；".join(turnaround_evidence),
                "turnaround_risks": "；".join(turnaround_risks),
                "financial_quality_score": round(financial_score, 2),
                "cashflow_quality_score": round(cashflow_score, 2),
                "balance_sheet_score": round(balance_score, 2),
                "growth_industry_score": round(growth_score, 2),
                "valuation_margin_score": round(valuation_score, 2),
                "total_score": round(max(total_score, 0.0), 2),
            }
        )

    return pd.DataFrame(records)


def rank_watchlists(df: pd.DataFrame, config: ScreenConfig) -> dict[str, pd.DataFrame]:
    clean = df[df["exclude_reason_count"] == 0].copy()
    clean = clean.sort_values(["total_score", "roe_avg_5y", "roic_avg_5y"], ascending=[False, False, False])

    result = {
        "排雷后全量": clean,
        "稳健价值型": clean[clean["stable_value_ok"]].head(config.top_per_category).copy(),
        "高质量成长型": clean[clean["high_quality_growth_ok"]].head(config.top_per_category).copy(),
        "高股息低估值型": clean[clean["high_dividend_ok"]].head(config.top_per_category).copy(),
        "困境反转型": clean[clean["turnaround_ok"]].head(config.top_per_category).copy(),
    }

    watch_union = pd.concat(
        [result["稳健价值型"], result["高质量成长型"], result["高股息低估值型"], result["困境反转型"]],
        ignore_index=True,
    )
    if not watch_union.empty:
        watch_union = watch_union.drop_duplicates(subset=["ts_code"]).sort_values("total_score", ascending=False)
    result["综合观察池"] = watch_union.head(config.overall_top_n).copy()
    return result


def format_percent(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}%"


def format_ratio(value: float | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}"


def format_yi(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}亿元"


def company_markdown(row: pd.Series) -> str:
    reasons: list[str] = []
    if row.get("stable_value_ok"):
        reasons.append("满足稳健价值型条件")
    if row.get("high_quality_growth_ok"):
        reasons.append("满足高质量成长型条件")
    if row.get("high_dividend_ok"):
        reasons.append("满足高股息低估值型条件")
    if row.get("turnaround_ok"):
        reasons.append("满足困境反转型条件")

    lines = [
        f"### {row['name']}（{row['ts_code']}）",
        "",
        "#### 1. 入选理由",
        f"- 综合评分 {row['total_score']:.1f} / 100，分类标签：{'、'.join(reasons) if reasons else '综合观察'}",
        f"- 最近 5 年平均 ROE {format_percent(row.get('roe_avg_5y'))}，平均 ROIC {format_percent(row.get('roic_avg_5y'))}",
        f"- 最近 5 年经营现金流累计 {format_yi(row.get('ocf_5y_yi'))}，净利润累计 {format_yi(row.get('net_income_5y_yi'))}，现金流/净利润 {format_ratio(row.get('ocf_net_income_ratio_5y'))}",
        f"- 当前 PE(TTM) {format_ratio(row.get('pe_ttm'))}，PB {format_ratio(row.get('pb'))}，股息率 {format_percent(row.get('dv_ttm'))}",
        f"- 资产负债率 {format_percent(row.get('debt_ratio_pct'))}，货币资金 {format_yi(row.get('money_cap_yi'))}，有息负债 {format_yi(row.get('interest_debt_yi'))}",
        "",
        "#### 2. 财务质量分析",
        f"- 毛利率 5 年均值 {format_percent(row.get('gross_margin_avg_5y'))}，净利率 5 年均值 {format_percent(row.get('net_margin_avg_5y'))}",
        f"- 扣非净利润 5 年 CAGR {format_percent(row.get('dt_profit_cagr_5y'))}，5 年中正值年份 {int(row.get('dt_profit_positive_years') or 0)} 年",
        f"- ROIC 相对行业均值：当前 {format_percent(row.get('roic_yearly') if pd.notna(row.get('roic_yearly')) else row.get('roic'))}，行业均值 {format_percent(row.get('industry_roic_avg'))}",
        "",
        "#### 3. 现金流分析",
        f"- 自由现金流 5 年累计 {format_yi(row.get('fcf_5y_yi'))}，正向年份 {int(row.get('fcf_positive_years') or 0)} 年",
        f"- 近 5 年经营现金流/扣非净利润 {format_ratio(row.get('ocf_dt_profit_ratio_5y'))}，分红现金覆盖倍数 {format_ratio(row.get('dividend_ocf_cover'))}",
        f"- 最近 5 年分红总额 {format_yi(row.get('dividend_5y_yi'))}，分红率均值 {format_percent(row.get('dividend_payout_mean_pct'))}",
        "",
        "#### 4. 资产负债表安全性",
        f"- 商誉/净资产 {format_percent(row.get('goodwill_to_equity_pct'))}，货币资金/短债 {format_ratio(row.get('cash_cover_short_debt'))}",
        f"- 风险标记：{row.get('risk_flags') or '无显著风险标记'}",
        "",
        "#### 5. 成长与行业空间",
        f"- 营收 5 年 CAGR {format_percent(row.get('revenue_cagr_5y'))}，扣非净利润 5 年 CAGR {format_percent(row.get('dt_profit_cagr_5y'))}",
        f"- 行业字段采用本地 `stock_basic.industry` 口径；行业空间评分使用行业内 ROIC 均值和最新增速做代理，不等同于供需格局研究。",
        "",
        "#### 6. 估值安全边际",
        f"- 估值窗口为 {row.get('valuation_window_start') or 'N/A'} 至 {row.get('valuation_window_end') or 'N/A'}，共 {int(row.get('valuation_trade_days') or 0)} 个交易日",
        f"- PE 分位 {format_percent(row.get('pe_percentile_window'))}，PB 分位 {format_percent(row.get('pb_percentile_window'))}，FCF Yield {format_percent(row.get('fcf_yield_pct'))}",
        "",
        "#### 7. 反转证据与失败风险",
        f"- 反转证据：{row.get('turnaround_evidence') or '未归类为困境反转'}",
        f"- 反转失败风险：{row.get('turnaround_risks') or '暂无显著反转失败信号'}",
        "",
    ]
    return "\n".join(lines)


def render_report(df: pd.DataFrame, ranked: dict[str, pd.DataFrame], config: ScreenConfig) -> str:
    clean = ranked["排雷后全量"]
    category_counts = {
        "稳健价值型": int(clean["stable_value_ok"].sum()),
        "高质量成长型": int(clean["high_quality_growth_ok"].sum()),
        "高股息低估值型": int(clean["high_dividend_ok"].sum()),
        "困境反转型": int(clean["turnaround_ok"].sum()),
    }
    excluded = df[df["exclude_reason_count"] > 0].copy()
    excluded_reason_stats = (
        excluded["exclude_reasons"].str.split("；").explode().value_counts().head(10).to_dict()
        if not excluded.empty
        else {}
    )

    sections = [
        "# A股价值观察池筛选结果",
        "",
        "## 数据口径",
        f"- 股票范围：本地库 `stock_basic` 中 `list_status='L'` 的 A 股，共 {len(df)} 家",
        f"- 最新估值日期：{df['data_trade_date'].dropna().max() if not df.empty else 'N/A'}",
        f"- 最新财报日期：{df['data_finance_end_date'].dropna().max() if not df.empty else 'N/A'}",
        f"- 审计意见最新口径：{df['audit_latest_end_date'].dropna().max() if 'audit_latest_end_date' in df else 'N/A'}",
        "- 估值历史窗口说明：当前库仅覆盖 `daily_basic` 的短窗口，因此 PE/PB 分位与中位数按可用交易日计算，不代表完整 5 年历史分位。",
        "- 大股东质押比例：本地库无字段，本次统一标记为待人工二次核验。",
        "",
        "## 默认筛选参数",
        "```json",
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        "```",
        "",
        "## 筛选概览",
        f"- 排雷后剩余：{len(clean)} 家",
        f"- 综合观察池：{len(ranked['综合观察池'])} 家",
        *[f"- {name}：{count} 家" for name, count in category_counts.items()],
        "",
        "## 主要排除原因",
    ]

    if excluded_reason_stats:
        sections.extend([f"- {reason}：{count} 家" for reason, count in excluded_reason_stats.items()])
    else:
        sections.append("- 无")

    sections.extend(
        [
            "",
            "## 综合观察池 Top",
        ]
    )

    if ranked["综合观察池"].empty:
        sections.append("- 暂无满足条件的公司")
    else:
        for _, row in ranked["综合观察池"].iterrows():
            sections.append(
                f"- {row['name']}（{row['ts_code']}） | 总分 {row['total_score']:.1f} | 行业 {row['industry']} | "
                f"ROE {format_percent(row.get('roe_avg_5y'))} | 股息率 {format_percent(row.get('dv_ttm'))}"
            )

    for category in ("稳健价值型", "高质量成长型", "高股息低估值型", "困境反转型"):
        sections.extend(["", f"## {category}"])
        frame = ranked[category]
        if frame.empty:
            sections.append("- 暂无满足条件的公司")
            continue
        for _, row in frame.iterrows():
            sections.append(company_markdown(row))

    return "\n".join(sections) + "\n"


def save_outputs(
    df: pd.DataFrame,
    ranked: dict[str, pd.DataFrame],
    config: ScreenConfig,
    prefix: str,
) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    asof_date = df["data_trade_date"].dropna().max() if not df.empty else "unknown"
    stem = f"{prefix}_{asof_date}"

    paths = {
        "all_csv": OUTPUT_DIR / f"{stem}_all.csv",
        "watchlist_csv": OUTPUT_DIR / f"{stem}_watchlist.csv",
        "report_md": OUTPUT_DIR / f"{stem}_report.md",
        "config_json": OUTPUT_DIR / f"{stem}_config.json",
        "summary_json": OUTPUT_DIR / f"{stem}_summary.json",
    }

    df.sort_values(["exclude_reason_count", "total_score"], ascending=[True, False]).to_csv(
        paths["all_csv"],
        index=False,
        encoding="utf-8-sig",
    )
    ranked["综合观察池"].to_csv(paths["watchlist_csv"], index=False, encoding="utf-8-sig")
    paths["report_md"].write_text(render_report(df, ranked, config), encoding="utf-8")
    paths["config_json"].write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    clean = ranked["排雷后全量"]
    summary = {
        "universe_count": int(len(df)),
        "post_risk_count": int(len(clean)),
        "watchlist_count": int(len(ranked["综合观察池"])),
        "eligible_stable_count": int(clean["stable_value_ok"].sum()),
        "eligible_growth_count": int(clean["high_quality_growth_ok"].sum()),
        "eligible_dividend_count": int(clean["high_dividend_ok"].sum()),
        "eligible_turnaround_count": int(clean["turnaround_ok"].sum()),
        "selected_stable_count": int(len(ranked["稳健价值型"])),
        "selected_growth_count": int(len(ranked["高质量成长型"])),
        "selected_dividend_count": int(len(ranked["高股息低估值型"])),
        "selected_turnaround_count": int(len(ranked["困境反转型"])),
        "trade_date": asof_date,
        "finance_end_date": df["data_finance_end_date"].dropna().max() if not df.empty else None,
    }
    paths["summary_json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return paths


def main() -> None:
    args = parse_args()
    config = build_config(args)
    engine = load_engine()
    frames = load_base_frames(engine)
    company_df = build_company_metrics(frames, config)

    if company_df.empty:
        raise RuntimeError("未从数据库中读取到可用公司数据。")

    ranked = rank_watchlists(company_df, config)
    paths = save_outputs(company_df, ranked, config, args.output_prefix)

    print(f"股票池总数: {len(company_df)}")
    print(f"排雷后剩余: {len(ranked['排雷后全量'])}")
    print(f"综合观察池: {len(ranked['综合观察池'])}")
    for name in ("稳健价值型", "高质量成长型", "高股息低估值型", "困境反转型"):
        print(f"{name}: {len(ranked[name])}")
    print(f"全量结果: {paths['all_csv']}")
    print(f"观察池结果: {paths['watchlist_csv']}")
    print(f"Markdown 报告: {paths['report_md']}")

    if not ranked["综合观察池"].empty:
        show_cols = [
            "ts_code",
            "name",
            "industry",
            "total_score",
            "roe_avg_5y",
            "roic_avg_5y",
            "dv_ttm",
            "pe_ttm",
            "pb",
        ]
        print(ranked["综合观察池"][show_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
