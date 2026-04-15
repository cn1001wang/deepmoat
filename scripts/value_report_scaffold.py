import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"


def slugify_symbol(ts_code: str) -> str:
    return ts_code.strip().upper().split(".", 1)[0]


def slugify_name(name: str) -> str:
    return re.sub(r"[\s/_-]+", "", str(name)).strip()


def short_timestamp() -> str:
    return pd.Timestamp.now().strftime("%y%m%d%H%M")


def load_engine():
    load_dotenv(dotenv_path=ROOT / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
    )
    db_url = database_url.replace("+psycopg2", "")
    return create_engine(db_url)


def query_df(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        return pd.read_sql(text(sql), engine, params=params or {})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"SQL 执行失败: {exc}") from exc


def format_yi(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value) / 1e8:.2f}亿"


def format_pct(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}%"


def format_num(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}"


def safe_div(a, b) -> Optional[float]:
    if pd.isna(a) or pd.isna(b) or not b:
        return None
    return float(a) / float(b)


def as_zero_if_nan(value) -> float:
    return 0.0 if value is None or pd.isna(value) else float(value)


def calc_growth(current, previous) -> Optional[float]:
    if pd.isna(current) or pd.isna(previous) or not previous:
        return None
    return (float(current) - float(previous)) / abs(float(previous)) * 100


def calc_cagr(values: list[float]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None and not pd.isna(v) and v > 0]
    if len(clean) < 2:
        return None
    periods = len(clean) - 1
    return (clean[-1] / clean[0]) ** (1 / periods) * 100 - 100


def normalize_query(raw: str) -> str:
    return raw.strip().upper()


def resolve_stock(engine, query: str) -> pd.Series:
    query = normalize_query(query)
    if "." in query:
        df = query_df(
            engine,
            """
            SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, c.main_business, c.chairman, c.manager, c.employees
            FROM stock_basic s
            LEFT JOIN stock_company c ON s.ts_code = c.ts_code
            WHERE s.ts_code = :query
            LIMIT 1
            """,
            {"query": query},
        )
        if not df.empty:
            return df.iloc[0]

    if query.isdigit() and len(query) == 6:
        df = query_df(
            engine,
            """
            SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, c.main_business, c.chairman, c.manager, c.employees
            FROM stock_basic s
            LEFT JOIN stock_company c ON s.ts_code = c.ts_code
            WHERE s.symbol = :symbol
            ORDER BY s.ts_code
            LIMIT 1
            """,
            {"symbol": query},
        )
        if not df.empty:
            return df.iloc[0]

    df = query_df(
        engine,
        """
        SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, c.main_business, c.chairman, c.manager, c.employees
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        WHERE s.name = :name
        ORDER BY s.ts_code
        LIMIT 1
        """,
        {"name": query},
    )
    if not df.empty:
        return df.iloc[0]

    fuzzy = query_df(
        engine,
        """
        SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, c.main_business, c.chairman, c.manager, c.employees
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        WHERE s.name LIKE :kw
        ORDER BY s.ts_code
        LIMIT 5
        """,
        {"kw": f"%{query}%"},
    )
    if not fuzzy.empty:
        picked = fuzzy.iloc[0]
        print(f"[提示] 未精确命中，已使用候选: {picked['name']} ({picked['ts_code']})")
        return picked

    raise ValueError(f"未找到股票: {query}")


def latest_by_end_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return (
        df.sort_values(["end_date", "ann_date"], ascending=[False, False])
        .drop_duplicates(subset=["end_date"], keep="first")
        .reset_index(drop=True)
    )


def fetch_bundle(engine, ts_code: str) -> dict:
    income = query_df(
        engine,
        """
        SELECT end_date, total_revenue, n_income_attr_p, sell_exp, admin_exp, fin_exp, rd_exp
        FROM income
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": ts_code},
    )
    balance = query_df(
        engine,
        """
        SELECT end_date, total_assets, total_liab, total_cur_assets, total_cur_liab, money_cap, inventories, accounts_receiv, st_borr, lt_borr, bond_payable
        FROM balancesheet
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": ts_code},
    )
    cash = query_df(
        engine,
        """
        SELECT end_date, n_cashflow_act, free_cashflow
        FROM cashflow
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": ts_code},
    )
    indicator = latest_by_end_date(
        query_df(
            engine,
            """
            SELECT end_date, ann_date, roe, roic, roa, grossprofit_margin, netprofit_margin, current_ratio, quick_ratio, debt_to_assets, ocf_to_profit, eps, bps, ar_turn, inv_turn, assets_turn, arturn_days, invturn_days
            FROM fina_indicator
            WHERE ts_code = :ts_code
            ORDER BY end_date DESC, ann_date DESC
            """,
            {"ts_code": ts_code},
        )
    )
    daily = query_df(
        engine,
        """
        SELECT trade_date, close, pe_ttm, pb, ps_ttm, dv_ttm, total_mv, circ_mv
        FROM daily_basic
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        {"ts_code": ts_code},
    )
    dividend = query_df(
        engine,
        """
        SELECT end_date, ann_date, ex_date, cash_div_tax
        FROM dividend
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC, ex_date DESC
        LIMIT 20
        """,
        {"ts_code": ts_code},
    )
    audit = query_df(
        engine,
        """
        SELECT end_date, audit_result, audit_agency
        FROM fina_audit
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
        LIMIT 10
        """,
        {"ts_code": ts_code},
    )
    mainbz = query_df(
        engine,
        """
        SELECT end_date, bz_item, bz_sales, bz_profit, bz_cost
        FROM fina_mainbz
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
        """,
        {"ts_code": ts_code},
    )
    return {
        "income": income,
        "balance": balance,
        "cash": cash,
        "indicator": indicator,
        "daily": daily,
        "dividend": dividend,
        "audit": audit,
        "mainbz": mainbz,
    }


def build_annual_table(bundle: dict) -> pd.DataFrame:
    income = bundle["income"]
    balance = bundle["balance"]
    cash = bundle["cash"]
    indicator = bundle["indicator"]

    annual_income = income[income["end_date"].str.endswith("1231")]
    annual_balance = balance[balance["end_date"].str.endswith("1231")]
    annual_cash = cash[cash["end_date"].str.endswith("1231")]
    annual_indicator = indicator[indicator["end_date"].str.endswith("1231")]

    annual = (
        annual_income.merge(annual_balance, on="end_date", how="left")
        .merge(annual_cash, on="end_date", how="left")
        .merge(annual_indicator, on="end_date", how="left")
        .sort_values("end_date", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )
    annual["revenue_yoy"] = annual["total_revenue"].shift(-1)
    annual["profit_yoy"] = annual["n_income_attr_p"].shift(-1)
    annual["revenue_yoy"] = annual.apply(
        lambda row: calc_growth(row["total_revenue"], row["revenue_yoy"]), axis=1
    )
    annual["profit_yoy"] = annual.apply(
        lambda row: calc_growth(row["n_income_attr_p"], row["profit_yoy"]), axis=1
    )
    annual["cfo_np_ratio"] = annual.apply(
        lambda row: safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) * 100
        if safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) is not None
        else None,
        axis=1,
    )
    for col in ["st_borr", "lt_borr", "bond_payable"]:
        annual[col] = pd.to_numeric(annual[col], errors="coerce")
    annual["interest_debt"] = annual["st_borr"].fillna(0.0) + annual["lt_borr"].fillna(0.0) + annual["bond_payable"].fillna(0.0)
    annual["net_cash"] = annual["money_cap"].fillna(0) - annual["interest_debt"].fillna(0)
    return annual


def build_latest_snapshot(bundle: dict) -> dict:
    income = bundle["income"]
    balance = bundle["balance"]
    cash = bundle["cash"]
    indicator = bundle["indicator"]

    if income.empty or balance.empty or cash.empty or indicator.empty:
        return {}

    end_date = income.iloc[0]["end_date"]
    income_row = income.iloc[0]
    balance_row = balance[balance["end_date"] == end_date].iloc[0]
    cash_row = cash[cash["end_date"] == end_date].iloc[0]
    ind_match = indicator[indicator["end_date"] == end_date]
    indicator_row = ind_match.iloc[0] if not ind_match.empty else indicator.iloc[0]
    prior = income[income["end_date"] == str(int(end_date) - 10000)]
    prior_cash = cash[cash["end_date"] == str(int(end_date) - 10000)]
    prior_row = prior.iloc[0] if not prior.empty else None
    prior_cash_row = prior_cash.iloc[0] if not prior_cash.empty else None

    interest_debt = (
        as_zero_if_nan(balance_row.get("st_borr"))
        + as_zero_if_nan(balance_row.get("lt_borr"))
        + as_zero_if_nan(balance_row.get("bond_payable"))
    )

    return {
        "end_date": end_date,
        "revenue": income_row["total_revenue"],
        "net_profit": income_row["n_income_attr_p"],
        "revenue_yoy": calc_growth(
            income_row["total_revenue"], prior_row["total_revenue"] if prior_row is not None else None
        ),
        "profit_yoy": calc_growth(
            income_row["n_income_attr_p"], prior_row["n_income_attr_p"] if prior_row is not None else None
        ),
        "cfo": cash_row["n_cashflow_act"],
        "cfo_yoy": calc_growth(
            cash_row["n_cashflow_act"], prior_cash_row["n_cashflow_act"] if prior_cash_row is not None else None
        ),
        "fcf": cash_row.get("free_cashflow"),
        "gross_margin": indicator_row.get("grossprofit_margin"),
        "net_margin": indicator_row.get("netprofit_margin"),
        "roe": indicator_row.get("roe"),
        "roic": indicator_row.get("roic"),
        "debt_to_assets": indicator_row.get("debt_to_assets"),
        "current_ratio": indicator_row.get("current_ratio"),
        "ocf_to_profit": indicator_row.get("ocf_to_profit"),
        "money_cap": balance_row.get("money_cap"),
        "interest_debt": interest_debt,
        "net_cash": as_zero_if_nan(balance_row.get("money_cap")) - interest_debt,
    }


def build_dividend_summary(dividend_df: pd.DataFrame) -> list[str]:
    if dividend_df.empty:
        return ["无分红数据"]
    executed = dividend_df[dividend_df["ex_date"].notna()].copy()
    if executed.empty:
        return ["有分红预案，但暂无已实施除权记录"]
    executed["year"] = executed["ex_date"].str[:4]
    yearly = executed.groupby("year", as_index=False)["cash_div_tax"].sum().sort_values("year", ascending=False)
    lines = []
    for _, row in yearly.head(5).iterrows():
        lines.append(f"{row['year']}年已实施现金分红（税前）合计：每股 {row['cash_div_tax']:.3f} 元")
    return lines


def annual_table_markdown(annual_df: pd.DataFrame) -> str:
    header = (
        "| 年度 | 营收 | 营收同比 | 归母净利 | 净利同比 | 毛利率 | 净利率 | ROE | ROIC | 资产负债率 | 经营现金流 | 自由现金流 | 现净比 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    rows: list[str] = []
    for _, row in annual_df.iterrows():
        rows.append(
            "| {year} | {revenue} | {rev_yoy} | {profit} | {np_yoy} | {gross} | {net} | {roe} | {roic} | {debt} | {cfo} | {fcf} | {cfo_np} |".format(
                year=row["end_date"][:4],
                revenue=format_yi(row["total_revenue"]),
                rev_yoy=format_pct(row["revenue_yoy"]),
                profit=format_yi(row["n_income_attr_p"]),
                np_yoy=format_pct(row["profit_yoy"]),
                gross=format_pct(row.get("grossprofit_margin")),
                net=format_pct(row.get("netprofit_margin")),
                roe=format_pct(row.get("roe")),
                roic=format_pct(row.get("roic")),
                debt=format_pct(row.get("debt_to_assets")),
                cfo=format_yi(row.get("n_cashflow_act")),
                fcf=format_yi(row.get("free_cashflow")),
                cfo_np=format_pct(row.get("cfo_np_ratio")),
            )
        )
    return "\n".join([header] + rows)


def to_yi_series(series: pd.Series) -> list[float]:
    return [round(float(v) / 1e8, 2) if pd.notna(v) else None for v in series]


def to_pct_series(series: pd.Series) -> list[float]:
    return [round(float(v), 2) if pd.notna(v) else None for v in series]


def classify_region_item(name: str) -> bool:
    if not name:
        return False
    region_keywords = [
        "地区",
        "华东",
        "华南",
        "华北",
        "华中",
        "西南",
        "西北",
        "东北",
        "境内",
        "境外",
        "海外",
        "国内",
        "国际",
        "北美",
        "欧洲",
        "亚太",
        "中国",
    ]
    return any(keyword in name for keyword in region_keywords)


def charts_from_mainbz(mainbz_df: pd.DataFrame) -> tuple[dict, dict, dict]:
    empty_pie = {
        "title": {"text": "分产品收入结构（数据待补）"},
        "tooltip": {"trigger": "item"},
        "legend": {"type": "scroll", "top": 24},
        "series": [{"type": "pie", "radius": "55%", "data": []}],
    }
    empty_stack = {
        "title": {"text": "分产品收入变化（数据待补）"},
        "tooltip": {"trigger": "axis"},
        "legend": {"type": "scroll", "top": 24, "data": []},
        "xAxis": {"type": "category", "data": []},
        "yAxis": {"type": "value", "name": "亿元"},
        "series": [],
    }
    empty_profit = {
        "title": {"text": "分产品利润结构（数据待补）"},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24, "data": ["利润", "毛利率"]},
        "xAxis": {"type": "category", "data": []},
        "yAxis": [{"type": "value", "name": "亿元"}, {"type": "value", "name": "%"}],
        "series": [{"name": "利润", "type": "bar", "data": []}, {"name": "毛利率", "type": "line", "yAxisIndex": 1, "data": []}],
    }
    if mainbz_df.empty:
        return empty_pie, empty_stack, empty_profit

    df = mainbz_df.copy()
    for col in ["bz_sales", "bz_profit", "bz_cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    latest_end = df["end_date"].max()
    latest = df[df["end_date"] == latest_end].copy()
    product_latest = latest[~latest["bz_item"].astype(str).apply(classify_region_item)]
    if product_latest.empty:
        product_latest = latest.copy()
    product_latest = (
        product_latest.groupby("bz_item", as_index=False)[["bz_sales", "bz_profit", "bz_cost"]]
        .sum()
        .sort_values("bz_sales", ascending=False)
        .head(8)
    )
    pie_option = {
        "title": {"text": f"分产品收入结构（{latest_end}）"},
        "tooltip": {"trigger": "item"},
        "legend": {"type": "scroll", "top": 24},
        "series": [
            {
                "type": "pie",
                "radius": "55%",
                "data": [
                    {"name": row["bz_item"], "value": round(float(row["bz_sales"]) / 1e8, 2)}
                    for _, row in product_latest.iterrows()
                    if pd.notna(row["bz_sales"])
                ],
            }
        ],
    }

    recent_years = sorted(df["end_date"].astype(str).str[:4].dropna().unique())[-5:]
    trend_df = df[df["end_date"].astype(str).str[:4].isin(recent_years)].copy()
    top_items = product_latest["bz_item"].tolist()[:5]
    pivot_sales = (
        trend_df[trend_df["bz_item"].isin(top_items)]
        .assign(year=trend_df["end_date"].astype(str).str[:4])
        .pivot_table(index="year", columns="bz_item", values="bz_sales", aggfunc="sum")
        .fillna(0)
        .sort_index()
    )
    stack_option = {
        "title": {"text": "分产品收入变化（近5年）"},
        "tooltip": {"trigger": "axis"},
        "legend": {"type": "scroll", "top": 24, "data": top_items},
        "xAxis": {"type": "category", "data": pivot_sales.index.tolist()},
        "yAxis": {"type": "value", "name": "亿元"},
        "series": [
            {
                "name": item,
                "type": "bar",
                "stack": "total",
                "data": [round(float(v) / 1e8, 2) for v in pivot_sales[item].tolist()],
            }
            for item in top_items
            if item in pivot_sales.columns
        ],
    }

    product_latest["margin"] = product_latest.apply(
        lambda row: safe_div(row["bz_profit"], row["bz_sales"]) * 100
        if safe_div(row["bz_profit"], row["bz_sales"]) is not None
        else None,
        axis=1,
    )
    profit_option = {
        "title": {"text": f"分产品利润结构（{latest_end}）"},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24, "data": ["利润", "毛利率"]},
        "xAxis": {"type": "category", "data": product_latest["bz_item"].tolist()},
        "yAxis": [{"type": "value", "name": "亿元"}, {"type": "value", "name": "%"}],
        "series": [
            {
                "name": "利润",
                "type": "bar",
                "data": [round(float(v) / 1e8, 2) if pd.notna(v) else None for v in product_latest["bz_profit"].tolist()],
            },
            {
                "name": "毛利率",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round(float(v), 2) if pd.notna(v) else None for v in product_latest["margin"].tolist()],
            },
        ],
    }
    return pie_option, stack_option, profit_option


def region_chart_from_mainbz(mainbz_df: pd.DataFrame) -> dict:
    if mainbz_df.empty:
        return {
            "title": {"text": "分地区收入分布（数据待补）"},
            "tooltip": {"trigger": "item"},
            "legend": {"type": "scroll", "top": 24},
            "series": [{"type": "pie", "radius": "55%", "data": []}],
        }
    df = mainbz_df.copy()
    df["bz_sales"] = pd.to_numeric(df["bz_sales"], errors="coerce")
    latest_end = df["end_date"].max()
    latest = df[df["end_date"] == latest_end].copy()
    region = latest[latest["bz_item"].astype(str).apply(classify_region_item)]
    if region.empty:
        return {
            "title": {"text": f"分地区收入分布（{latest_end}，数据待补）"},
            "tooltip": {"trigger": "item"},
            "legend": {"type": "scroll", "top": 24},
            "series": [{"type": "pie", "radius": "55%", "data": []}],
        }
    region_group = region.groupby("bz_item", as_index=False)["bz_sales"].sum().sort_values("bz_sales", ascending=False)
    return {
        "title": {"text": f"分地区收入分布（{latest_end}）"},
        "tooltip": {"trigger": "item"},
        "legend": {"type": "scroll", "top": 24},
        "series": [
            {
                "type": "pie",
                "radius": "55%",
                "data": [
                    {"name": row["bz_item"], "value": round(float(row["bz_sales"]) / 1e8, 2)}
                    for _, row in region_group.iterrows()
                    if pd.notna(row["bz_sales"])
                ],
            }
        ],
    }


def build_echarts_options(annual_df: pd.DataFrame, bundle: dict) -> list[tuple[str, dict]]:
    asc = annual_df.sort_values("end_date").copy()
    years = asc["end_date"].astype(str).str[:4].tolist()
    revenue = to_yi_series(asc["total_revenue"])
    net_profit = to_yi_series(asc["n_income_attr_p"])
    gross_margin = to_pct_series(asc["grossprofit_margin"])
    net_margin = to_pct_series(asc["netprofit_margin"])
    total_assets = to_yi_series(asc["total_assets"])
    total_liab = to_yi_series(asc["total_liab"])
    equity = [round((float(a) - float(b)) / 1e8, 2) if pd.notna(a) and pd.notna(b) else None for a, b in zip(asc["total_assets"], asc["total_liab"])]
    ocf = to_yi_series(asc["n_cashflow_act"])
    fcf = to_yi_series(asc["free_cashflow"])
    eps = to_pct_series(asc["eps"])
    roe = to_pct_series(asc["roe"])
    roa = to_pct_series(asc["roa"])
    debt_ratio = to_pct_series(asc["debt_to_assets"])
    current_ratio = to_pct_series(asc["current_ratio"])
    quick_ratio = to_pct_series(asc["quick_ratio"])
    ar_turn = to_pct_series(asc["ar_turn"])
    inv_turn = to_pct_series(asc["inv_turn"])

    options: list[tuple[str, dict]] = []

    options.append(
        (
            "1. 主营业务收入趋势图",
            {
                "title": {"text": "主营业务收入趋势（近5年）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["主营业务收入"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "亿元"},
                "series": [{"name": "主营业务收入", "type": "line", "smooth": True, "data": revenue}],
            },
        )
    )
    options.append(
        (
            "2. 净利润趋势图",
            {
                "title": {"text": "净利润趋势（近5年）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["净利润", "营业收入"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": [{"type": "value", "name": "亿元"}, {"type": "value", "name": "亿元"}],
                "series": [
                    {"name": "净利润", "type": "bar", "data": net_profit},
                    {"name": "营业收入", "type": "line", "yAxisIndex": 1, "data": revenue},
                ],
            },
        )
    )
    options.append(
        (
            "3. 毛利率和净利率对比图",
            {
                "title": {"text": "毛利率 vs 净利率"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["毛利率", "净利率"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "%"},
                "series": [
                    {"name": "毛利率", "type": "bar", "data": gross_margin},
                    {"name": "净利率", "type": "bar", "data": net_margin},
                ],
            },
        )
    )

    product_revenue_option, product_sales_trend_option, product_profit_option = charts_from_mainbz(bundle["mainbz"])
    options.append(("4. 分产品收入结构图", product_revenue_option))
    options.append(("4. 分产品收入变化图", product_sales_trend_option))
    options.append(("5. 分产品利润结构图", product_profit_option))
    options.append(("6. 分地区收入分布图", region_chart_from_mainbz(bundle["mainbz"])))

    options.append(
        (
            "7. 资产负债表关键数据图",
            {
                "title": {"text": "资产负债表关键数据（近5年）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["总资产", "总负债", "股东权益"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "亿元"},
                "series": [
                    {"name": "总资产", "type": "bar", "stack": "capital", "data": total_assets},
                    {"name": "总负债", "type": "bar", "stack": "capital", "data": total_liab},
                    {"name": "股东权益", "type": "line", "data": equity},
                ],
            },
        )
    )

    options.append(
        (
            "8. 自由现金流与经营现金流对比图",
            {
                "title": {"text": "自由现金流 vs 经营现金流"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["经营现金流", "自由现金流"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "亿元"},
                "series": [
                    {"name": "经营现金流", "type": "line", "data": ocf},
                    {"name": "自由现金流", "type": "line", "data": fcf},
                ],
            },
        )
    )

    div_df = bundle["dividend"]
    div_by_year = {}
    if not div_df.empty:
        executed = div_df[div_df["ex_date"].notna()].copy()
        if not executed.empty:
            executed["year"] = executed["ex_date"].astype(str).str[:4]
            div_by_year = executed.groupby("year")["cash_div_tax"].sum().to_dict()
    div_per_share = [round(float(div_by_year.get(year, 0.0)), 3) for year in years]

    options.append(
        (
            "9. 股东回报分析图",
            {
                "title": {"text": "股东回报（EPS/分红）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["EPS", "每股现金分红（已实施）"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "元"},
                "series": [
                    {"name": "EPS", "type": "line", "data": eps},
                    {"name": "每股现金分红（已实施）", "type": "line", "data": div_per_share},
                ],
            },
        )
    )

    options.append(
        (
            "10. 财务比率分析图",
            {
                "title": {"text": "关键财务比率（近5年）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"type": "scroll", "top": 24, "data": ["资产负债率", "流动比率", "速动比率", "应收周转率", "存货周转率"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": [{"type": "value", "name": "比率/%"}, {"type": "value", "name": "周转率"}],
                "series": [
                    {"name": "资产负债率", "type": "line", "data": debt_ratio},
                    {"name": "流动比率", "type": "line", "data": current_ratio},
                    {"name": "速动比率", "type": "line", "data": quick_ratio},
                    {"name": "应收周转率", "type": "bar", "yAxisIndex": 1, "data": ar_turn},
                    {"name": "存货周转率", "type": "bar", "yAxisIndex": 1, "data": inv_turn},
                ],
            },
        )
    )

    options.append(
        (
            "11. ROE与ROA对比图",
            {
                "title": {"text": "ROE vs ROA（近5年）"},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 24, "data": ["ROE", "ROA"]},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "name": "%"},
                "series": [
                    {"name": "ROE", "type": "line", "data": roe},
                    {"name": "ROA", "type": "line", "data": roa},
                ],
            },
        )
    )

    return options


def echarts_section_markdown(annual_df: pd.DataFrame, bundle: dict) -> str:
    blocks = ["## ECharts 图表数据（option）", "- 说明：以下 `option` 可直接用于前端图表渲染；单位已在坐标轴标注。"]
    for title, option in build_echarts_options(annual_df, bundle):
        blocks.append(f"### {title}\n```json\n{json.dumps(option, ensure_ascii=False, indent=2)}\n```")
    return "\n\n".join(blocks)


def render_report(stock_row: pd.Series, bundle: dict, annual_df: pd.DataFrame, latest: dict, include_echarts: bool = True) -> str:
    ts_code = stock_row["ts_code"]
    name = stock_row["name"]
    daily = bundle["daily"].iloc[0] if not bundle["daily"].empty else None
    dividend_lines = build_dividend_summary(bundle["dividend"])
    audit_df = bundle["audit"]

    cagr_window = list(reversed(annual_df["total_revenue"].tolist()))
    revenue_cagr = calc_cagr(cagr_window)
    profit_cagr = calc_cagr(list(reversed(annual_df["n_income_attr_p"].tolist())))

    valuation_lines = ["- 无估值数据"] if daily is None else [
        f"- 交易日：{daily['trade_date']}",
        f"- 收盘价：{daily['close']:.2f} 元",
        f"- PE(TTM)：{daily['pe_ttm']:.2f} 倍",
        f"- PB：{daily['pb']:.2f} 倍",
        f"- PS(TTM)：{daily['ps_ttm']:.2f} 倍",
        f"- 股息率(TTM)：{daily['dv_ttm']:.2f}%",
        f"- 总市值：{daily['total_mv'] / 10000:.2f} 亿元",
    ]

    latest_lines = ["- 最新报告期数据缺失"] if not latest else [
        f"- 报告期：{latest['end_date']}",
        f"- 营收：{format_yi(latest['revenue'])}（同比 {format_pct(latest['revenue_yoy'])}）",
        f"- 归母净利润：{format_yi(latest['net_profit'])}（同比 {format_pct(latest['profit_yoy'])}）",
        f"- 经营现金流：{format_yi(latest['cfo'])}（同比 {format_pct(latest['cfo_yoy'])}）",
        f"- 自由现金流：{format_yi(latest['fcf'])}",
        f"- 毛利率：{format_pct(latest['gross_margin'])}，净利率：{format_pct(latest['net_margin'])}",
        f"- ROE：{format_pct(latest['roe'])}，ROIC：{format_pct(latest['roic'])}",
        f"- 资产负债率：{format_pct(latest['debt_to_assets'])}，流动比率：{format_num(latest['current_ratio'])}",
        f"- 经营现金流/利润：{format_pct(latest['ocf_to_profit'])}",
        f"- 货币资金：{format_yi(latest['money_cap'])}，有息负债：{format_yi(latest['interest_debt'])}，净现金：{format_yi(latest['net_cash'])}",
    ]

    audit_lines = ["- 审计数据缺失"]
    if not audit_df.empty:
        audit_lines = [
            f"- {row['end_date']}：{row['audit_result']}（{row['audit_agency']}）"
            for _, row in audit_df.head(5).iterrows()
        ]

    sections = [
        f"# {name}（{ts_code}）价值分析报告草稿",
        "\n".join(
            [
                f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "- 自动化脚本：`scripts/value_report_scaffold.py`",
                "- 数据口径：数据库字段定义以 `app/models/models.py` 为准",
                f"- 公司信息：行业 {stock_row['industry']}｜地区 {stock_row['area']}｜上市日期 {stock_row['list_date']}",
                f"- 管理层：董事长 {stock_row.get('chairman') or 'N/A'}｜总经理 {stock_row.get('manager') or 'N/A'}｜员工 {stock_row.get('employees') or 'N/A'}",
                f"- 主营业务：{stock_row.get('main_business') or 'N/A'}",
                "- 提示：本文件已自动填充定量部分，定性模块请结合最新公告与行业资料补充。",
            ]
        ),
        "## 自动填充数据（可直接引用）\n### 最新估值\n" + "\n".join(valuation_lines),
        "### 最新财务快照\n" + "\n".join(latest_lines),
        "### 近五年年报趋势\n"
        + annual_table_markdown(annual_df)
        + f"\n\n- 近五年营收CAGR：{format_pct(revenue_cagr)}\n- 近五年净利CAGR：{format_pct(profit_cagr)}",
        "### 分红与审计\n#### 已实施分红\n"
        + "\n".join(dividend_lines)
        + "\n\n#### 审计意见\n"
        + "\n".join(audit_lines),
    ]
    if include_echarts:
        sections.append(echarts_section_markdown(annual_df, bundle))
    sections.extend(
        [
            """## 1. 公司概况（商业模式优先）
- 公司是如何赚钱的？
- 收入来源构成（核心业务占比）
- 客户类型（To B / To C / 政府）
- 是否具备持续性收入（一次性 vs 订阅/复购）
- 是否依赖单一客户或区域

### 结论
- 商业模式是否简单、可理解
- 是否具备长期可持续性""",
            """## 2. 行业与竞争格局
- 行业空间（市场规模、天花板）
- 行业阶段（成长 / 成熟 / 衰退）
- 行业增速
- 主要竞争对手
- 市场份额与行业集中度
- 公司在产业链中的位置

### 结论
- 是否属于优质赛道
- 公司是否处于有利竞争位置
- 行业未来3-5年趋势""",
            """## 3. 护城河分析（含真伪辨别）
- 品牌优势
- 成本优势
- 网络效应
- 转换成本
- 技术壁垒
- 渠道优势

### 护城河真伪辨别
- 如果产品提价 5%，客户是否会流失？
- 客户是否对价格敏感？
- 是否存在“非它不可”的使用场景？
- 替代品是否容易出现？
- 客户更换供应商的成本高不高？

### 结论
- 护城河类型
- 护城河强度：强 / 中 / 弱 / 伪护城河
- 是否具备真实定价权""",
            """## 4. 管理层与资本配置（重点）
- 管理层背景与稳定性
- 是否存在诚信问题（造假 / 处罚 / 诉讼）
- 过往战略是否理性

### 资本配置历史
- 是否长期分红
- 是否进行回购注销（而非股权激励稀释）
- 并购历史（成功 / 失败 / 频繁）
- 是否存在盲目多元化扩张
- 资本开支是否合理

### 结论
- 管理层类型：价值创造者 / 中性 / 价值毁灭者
- 是否值得长期信任""",
            """## 5. 财务分析
### 5.1 成长性
- 营收增长率（近3-5年）
- 净利润增长率
- 增长是否稳定

### 结论
- 是否具备持续成长能力

### 5.2 盈利能力
- 毛利率
- 净利率
- ROE / ROIC

### 结论
- 是否具备定价权
- 盈利质量如何

### 5.3 财务健康
- 资产负债率
- 有息负债
- 现金储备
- 短期偿债能力

### 结论
- 是否存在财务风险

### 5.4 现金流质量
- 经营现金流
- 自由现金流
- 净利润与现金流是否匹配

### 结论
- 利润是否真实
- 是否具备造血能力""",
            """## 6. 成长驱动
- 未来3-5年增长来源
- 是否依赖提价 / 扩张 / 新业务
- 增长逻辑是否清晰

### 结论
- 成长是否可持续""",
            """## 7. 风险分析（含幸存者偏差）
- 政策风险
- 行业竞争风险
- 技术替代风险
- 财务风险
- 客户集中风险

### 幸存者偏差检验
- 行业历史最差时期是什么时候？
- 当时发生了什么（金融危机 / 疫情 / 监管）？
- 公司当时表现：是否大幅亏损 / 现金流断裂 / 接近破产？
- 公司在极端情况下是：变强 / 持平 / 衰退

### 结论
- 抗风险能力：强 / 中 / 弱
- 是否属于“穿越周期公司”""",
            """## 8. 估值分析
- PE / PB / PS / PEG / EV/EBITDA
- 当前估值 vs 历史估值
- 当前估值 vs 行业对比

### 结论
- 当前是否高估 / 低估 / 合理
- 是否具备安全边际""",
            """## 9. 投资判断
### 多头逻辑
1. 
2. 
3. 

### 空头逻辑
1. 
2. 
3. 

### 核心跟踪指标
1. 
2. 
3. """,
            """## 最终结论
- 这是否是一家好公司？
- 是否具备长期投资价值？
- 当前价格是否值得买入？
- 投资建议：买入 / 观察 / 回避""",
            """## 总评分（100分）
- 商业模式：
- 护城河：
- 管理层：
- 财务：
- 风险：
- 估值：

**最终评分：__ / 100**""",
            """## 三个终极问题（必须回答）
1. 如果提价 5%，客户会不会流失？
2. 公司赚的钱有没有被管理层浪费？
3. 在行业最差年份，公司是怎么活下来的？""",
        ]
    )
    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="生成价值分析报告草稿（巴菲特+芒格模板）")
    parser.add_argument("query", help="股票代码（如 600519.SH / 600519）或公司名称（如 贵州茅台）")
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="输出目录，默认 outputs",
    )
    args = parser.parse_args()

    engine = load_engine()
    stock_row = resolve_stock(engine, args.query)
    ts_code = stock_row["ts_code"]
    bundle = fetch_bundle(engine, ts_code)

    required = ["income", "balance", "cash", "indicator", "daily"]
    missing = [name for name in required if bundle[name].empty]
    if missing:
        raise RuntimeError(f"{ts_code} 缺少核心数据表：{', '.join(missing)}")

    annual_df = build_annual_table(bundle)
    latest = build_latest_snapshot(bundle)
    report = render_report(stock_row, bundle, annual_df, latest)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    code_slug = slugify_symbol(ts_code)
    name_slug = slugify_name(stock_row["name"])
    timestamp = short_timestamp()
    output_path = output_dir / f"value_{code_slug}_{name_slug}_{timestamp}_draft.md"
    output_path.write_text(report, encoding="utf-8")

    print(f"报告草稿已生成: {output_path}")


if __name__ == "__main__":
    main()
