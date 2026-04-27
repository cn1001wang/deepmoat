"""
作用：
按单只股票生成结构化文本分析，整合利润表、资产负债表、现金流、估值和主营业务，
适合快速产出一个可读的基本面摘要报告。
"""

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


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


def query_df(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        return pd.read_sql(text(sql), engine, params=params or {})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"SQL 执行失败: {exc}") from exc


def latest_by_end_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    sort_cols = [col for col in ["end_date", "ann_date"] if col in df.columns]
    ascending = [False] * len(sort_cols)
    return (
        df.sort_values(sort_cols, ascending=ascending)
        .drop_duplicates(subset=["end_date"], keep="first")
        .reset_index(drop=True)
    )


def format_yi(value) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{float(value) / 1e8:.2f}亿"


def format_pct(value) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}%"


def format_num(value) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}"


def safe_div(a, b):
    if pd.isna(a) or pd.isna(b) or not b:
        return None
    return float(a) / float(b)


def calc_growth(current, previous):
    if pd.isna(current) or pd.isna(previous) or not previous:
        return None
    return (float(current) - float(previous)) / abs(float(previous)) * 100


def build_annual_table(income_df, balance_df, cash_df, indicator_df) -> pd.DataFrame:
    annual_income = income_df[income_df["end_date"].str.endswith("1231")].copy()
    annual_balance = balance_df[balance_df["end_date"].str.endswith("1231")].copy()
    annual_cash = cash_df[cash_df["end_date"].str.endswith("1231")].copy()
    annual_indicator = indicator_df[indicator_df["end_date"].str.endswith("1231")].copy()

    annual = (
        annual_income.merge(annual_balance, on="end_date", how="left", suffixes=("", "_bal"))
        .merge(annual_cash, on="end_date", how="left", suffixes=("", "_cash"))
        .merge(annual_indicator, on="end_date", how="left", suffixes=("", "_ind"))
    )
    annual = annual.sort_values("end_date", ascending=False).reset_index(drop=True)
    annual["revenue_yoy"] = annual["total_revenue"].shift(-1)
    annual["profit_yoy"] = annual["n_income_attr_p"].shift(-1)
    annual["revenue_yoy"] = annual.apply(
        lambda row: calc_growth(row["total_revenue"], row["revenue_yoy"]), axis=1
    )
    annual["profit_yoy"] = annual.apply(
        lambda row: calc_growth(row["n_income_attr_p"], row["profit_yoy"]), axis=1
    )
    annual["ocf_profit_ratio"] = annual.apply(
        lambda row: safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) * 100
        if safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) is not None
        else None,
        axis=1,
    )
    annual["cash_current_liab_ratio"] = annual.apply(
        lambda row: safe_div(row["money_cap"], row["total_cur_liab"]) * 100
        if safe_div(row["money_cap"], row["total_cur_liab"]) is not None
        else None,
        axis=1,
    )
    return annual.head(5)


def build_quarter_snapshot(income_df, balance_df, cash_df, indicator_df):
    latest_income = income_df.iloc[0]
    latest_balance = balance_df.iloc[0]
    latest_cash = cash_df.iloc[0]
    latest_indicator = indicator_df.iloc[0]

    current_end = latest_income["end_date"]
    prior = income_df[income_df["end_date"] == str(int(current_end) - 10000)]
    prior_income = prior.iloc[0] if not prior.empty else None
    prior_cash = cash_df[cash_df["end_date"] == str(int(current_end) - 10000)]
    prior_cash = prior_cash.iloc[0] if not prior_cash.empty else None

    revenue_yoy = (
        calc_growth(latest_income["total_revenue"], prior_income["total_revenue"])
        if prior_income is not None
        else None
    )
    profit_yoy = (
        calc_growth(latest_income["n_income_attr_p"], prior_income["n_income_attr_p"])
        if prior_income is not None
        else None
    )
    ocf_yoy = (
        calc_growth(latest_cash["n_cashflow_act"], prior_cash["n_cashflow_act"])
        if prior_cash is not None
        else None
    )
    expense_ratio = None
    expenses = sum(
        float(latest_income[col] or 0)
        for col in ["sell_exp", "admin_exp", "fin_exp", "rd_exp"]
    )
    if latest_income["total_revenue"]:
        expense_ratio = expenses / float(latest_income["total_revenue"]) * 100

    return {
        "end_date": current_end,
        "revenue": latest_income["total_revenue"],
        "net_profit": latest_income["n_income_attr_p"],
        "revenue_yoy": revenue_yoy,
        "profit_yoy": profit_yoy,
        "ocf": latest_cash["n_cashflow_act"],
        "ocf_yoy": ocf_yoy,
        "gross_margin": latest_indicator.get("grossprofit_margin"),
        "net_margin": latest_indicator.get("netprofit_margin"),
        "roe": latest_indicator.get("roe"),
        "roa": latest_indicator.get("roa"),
        "current_ratio": latest_indicator.get("current_ratio"),
        "debt_to_assets": latest_indicator.get("debt_to_assets"),
        "ocf_to_profit": latest_indicator.get("ocf_to_profit"),
        "cash_current_liab_ratio": (
            safe_div(latest_balance["money_cap"], latest_balance["total_cur_liab"]) * 100
            if safe_div(latest_balance["money_cap"], latest_balance["total_cur_liab"]) is not None
            else None
        ),
        "expense_ratio": expense_ratio,
        "inventory": latest_balance["inventories"],
        "accounts_receiv": latest_balance["accounts_receiv"],
    }


def summarize_dividend(dividend_df: pd.DataFrame) -> list[str]:
    if dividend_df.empty:
        return ["近年分红数据缺失"]
    dedup = (
        dividend_df.sort_values(["end_date", "ann_date", "ex_date"], ascending=False)
        .drop_duplicates(subset=["end_date"], keep="first")
        .head(5)
    )
    lines = []
    for _, row in dedup.iterrows():
        cash = row["cash_div_tax"]
        ex_date = row["ex_date"] if pd.notna(row["ex_date"]) else "未披露除权日"
        lines.append(f"{row['end_date']}: 每股现金分红 {cash:.2f} 元，除权日 {ex_date}")
    return lines


def summarize_audit(audit_df: pd.DataFrame) -> list[str]:
    if audit_df.empty:
        return ["审计意见数据缺失"]
    return [
        f"{row['end_date']}: {row['audit_result']}（{row['audit_agency']}）"
        for _, row in audit_df.head(5).iterrows()
    ]


def build_core_view(annual_df: pd.DataFrame, quarter: dict, daily_row: pd.Series) -> list[str]:
    bullets = []
    if not annual_df.empty:
        latest_annual = annual_df.iloc[0]
        if pd.notna(latest_annual.get("roe")) and latest_annual["roe"] >= 20:
            bullets.append(
                f"2024 年 ROE 达 {latest_annual['roe']:.2f}%，盈利质量处于高位。"
            )
        if (
            pd.notna(latest_annual.get("ocf_profit_ratio"))
            and latest_annual["ocf_profit_ratio"] >= 100
        ):
            bullets.append(
                f"2024 年经营现金流/归母净利润约 {latest_annual['ocf_profit_ratio']:.1f}%，利润兑现度较强。"
            )
        if (
            pd.notna(latest_annual.get("debt_to_assets"))
            and latest_annual["debt_to_assets"] < 35
        ):
            bullets.append(
                f"2024 年资产负债率 {latest_annual['debt_to_assets']:.2f}%，杠杆水平偏低。"
            )
    if quarter["profit_yoy"] is not None and quarter["profit_yoy"] > 20:
        bullets.append(
            f"截至 {quarter['end_date']}，归母净利润同比增长 {quarter['profit_yoy']:.2f}%，景气延续。"
        )
    if pd.notna(daily_row.get("pe_ttm")) and daily_row["pe_ttm"] < 20:
        bullets.append(
            f"按 {daily_row['trade_date']} 收盘口径，PE(TTM) 约 {daily_row['pe_ttm']:.2f} 倍，估值不算激进。"
        )
    if not bullets:
        bullets.append("当前财务表现中性，需要继续观察行业价格与新增产能消化。")
    return bullets


def build_risks(quarter: dict, annual_df: pd.DataFrame, daily_row: pd.Series) -> list[str]:
    risks = [
        "维生素、蛋氨酸和香精香料均有周期属性，行业价格回落会直接压缩毛利率。",
        "公司处于持续扩产和项目推进阶段，若需求不及预期，新增产能消化节奏会拖累回报率。",
    ]
    if quarter["expense_ratio"] is not None and quarter["expense_ratio"] > 10:
        risks.append(
            f"最新报告期期间费用率约 {quarter['expense_ratio']:.2f}%，需跟踪研发与管理投入回收效率。"
        )
    if not annual_df.empty and pd.notna(annual_df.iloc[0].get("cash_current_liab_ratio")):
        ratio = annual_df.iloc[0]["cash_current_liab_ratio"]
        if ratio < 100:
            risks.append(f"货币资金/流动负债约 {ratio:.1f}%，短债安全边际仍需结合经营现金流跟踪。")
    if pd.notna(daily_row.get("dv_ttm")) and daily_row["dv_ttm"] < 2:
        risks.append(
            f"当前股息率(TTM) 约 {daily_row['dv_ttm']:.2f}%，对纯高股息资金的吸引力一般。"
        )
    return risks


def annual_table_markdown(annual_df: pd.DataFrame) -> str:
    header = (
        "| 年度 | 营收 | 营收同比 | 归母净利 | 净利同比 | ROE | ROA | 毛利率 | 资产负债率 | 流动比率 | 经营现金流 | 现净比 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    rows = []
    for _, row in annual_df.iterrows():
        rows.append(
            "| {year} | {revenue} | {revenue_yoy} | {profit} | {profit_yoy} | {roe} | {roa} | {gross} | {debt} | {current} | {ocf} | {ocf_profit} |".format(
                year=row["end_date"][:4],
                revenue=format_yi(row["total_revenue"]),
                revenue_yoy=format_pct(row["revenue_yoy"]),
                profit=format_yi(row["n_income_attr_p"]),
                profit_yoy=format_pct(row["profit_yoy"]),
                roe=format_pct(row["roe"]),
                roa=format_pct(row["roa"]),
                gross=format_pct(row["grossprofit_margin"]),
                debt=format_pct(row["debt_to_assets"]),
                current=format_num(row["current_ratio"]),
                ocf=format_yi(row["n_cashflow_act"]),
                ocf_profit=format_pct(row["ocf_profit_ratio"]),
            )
        )
    return "\n".join([header] + rows)


def build_report(ts_code: str, stock_row, daily_row, annual_df, quarter, dividend_lines, audit_lines) -> str:
    title = f"# 新和成（{ts_code}）基本面分析报告"
    meta = [
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 公司：{stock_row['name']}，行业：{stock_row['industry']}，地区：{stock_row['area']}，上市日期：{stock_row['list_date']}",
        f"- 主营业务：{stock_row['main_business']}",
        "- 数据口径：数据库字段定义以 `app/models/models.py` 为准，核心表使用 `income`、`balancesheet`、`cashflow`、`daily_basic`、`fina_indicator`、`fina_audit`、`dividend`。",
    ]

    valuation = [
        f"- 最新交易日：{daily_row['trade_date']}",
        f"- 收盘价：{daily_row['close']:.2f} 元",
        f"- PE(TTM)：{daily_row['pe_ttm']:.2f} 倍",
        f"- PB：{daily_row['pb']:.2f} 倍",
        f"- PS(TTM)：{daily_row['ps_ttm']:.2f} 倍",
        f"- 股息率(TTM)：{daily_row['dv_ttm']:.2f}%",
        f"- 总市值：{daily_row['total_mv'] / 10000:.2f} 亿元",
        f"- 流通市值：{daily_row['circ_mv'] / 10000:.2f} 亿元",
    ]

    quarter_lines = [
        f"- 报告期：{quarter['end_date']}",
        f"- 营收：{format_yi(quarter['revenue'])}，同比 {format_pct(quarter['revenue_yoy'])}",
        f"- 归母净利润：{format_yi(quarter['net_profit'])}，同比 {format_pct(quarter['profit_yoy'])}",
        f"- 经营现金流：{format_yi(quarter['ocf'])}，同比 {format_pct(quarter['ocf_yoy'])}",
        f"- ROE：{format_pct(quarter['roe'])}，ROA：{format_pct(quarter['roa'])}",
        f"- 毛利率：{format_pct(quarter['gross_margin'])}，净利率：{format_pct(quarter['net_margin'])}",
        f"- 资产负债率：{format_pct(quarter['debt_to_assets'])}，流动比率：{format_num(quarter['current_ratio'])}",
        f"- 经营现金流/营业利润：{format_pct(quarter['ocf_to_profit'])}",
        f"- 货币资金/流动负债：{format_pct(quarter['cash_current_liab_ratio'])}",
        f"- 期间费用率：{format_pct(quarter['expense_ratio'])}",
        f"- 存货：{format_yi(quarter['inventory'])}，应收账款：{format_yi(quarter['accounts_receiv'])}",
    ]

    core_view = "\n".join(f"- {item}" for item in build_core_view(annual_df, quarter, daily_row))
    risks = "\n".join(f"- {item}" for item in build_risks(quarter, annual_df, daily_row))
    dividends = "\n".join(f"- {item}" for item in dividend_lines)
    audits = "\n".join(f"- {item}" for item in audit_lines)

    return "\n\n".join(
        [
            title,
            "\n".join(meta),
            "## 核心结论\n" + core_view,
            "## 最新估值\n" + "\n".join(valuation),
            "## 最新财务快照\n" + "\n".join(quarter_lines),
            "## 近五年年报趋势\n" + annual_table_markdown(annual_df),
            "## 分红与审计\n### 分红\n" + dividends + "\n\n### 审计意见\n" + audits,
            "## 风险提示\n" + risks,
        ]
    )


def main():
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/analyze_stock_report.py 002001.SZ")
        sys.exit(1)

    ts_code = sys.argv[1].strip().upper()
    engine = load_engine()

    stock_sql = """
        SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, c.main_business
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        WHERE s.ts_code = :ts_code
        LIMIT 1
    """
    income_sql = """
        SELECT end_date, total_revenue, n_income_attr_p, oper_cost, sell_exp, admin_exp, fin_exp, rd_exp
        FROM income
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
    """
    balance_sql = """
        SELECT end_date, total_assets, total_liab, total_cur_assets, total_cur_liab, money_cap, inventories, accounts_receiv
        FROM balancesheet
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
    """
    cash_sql = """
        SELECT end_date, n_cashflow_act, free_cashflow, n_cashflow_inv_act, n_cash_flows_fnc_act, n_incr_cash_cash_equ
        FROM cashflow
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
    """
    indicator_sql = """
        SELECT end_date, ann_date, roe, roe_waa, roa, grossprofit_margin, netprofit_margin,
               current_ratio, debt_to_assets, assets_turn, ocf_to_or, ocf_to_opincome,
               ocf_to_profit, or_yoy, netprofit_yoy, dt_netprofit_yoy, bps, eps
        FROM fina_indicator
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC
    """
    daily_sql = """
        SELECT trade_date, close, pe_ttm, pb, ps_ttm, dv_ttm, total_mv, circ_mv, turnover_rate, volume_ratio
        FROM daily_basic
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
        LIMIT 1
    """
    dividend_sql = """
        SELECT end_date, ann_date, ex_date, cash_div_tax, stk_bo_rate, stk_co_rate
        FROM dividend
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC, ex_date DESC
    """
    audit_sql = """
        SELECT end_date, audit_result, audit_agency
        FROM fina_audit
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
    """

    stock_df = query_df(engine, stock_sql, {"ts_code": ts_code})
    if stock_df.empty:
        print(f"未找到 {ts_code} 的基础信息。")
        sys.exit(1)

    income_df = query_df(engine, income_sql, {"ts_code": ts_code})
    balance_df = query_df(engine, balance_sql, {"ts_code": ts_code})
    cash_df = query_df(engine, cash_sql, {"ts_code": ts_code})
    indicator_df = latest_by_end_date(query_df(engine, indicator_sql, {"ts_code": ts_code}))
    daily_df = query_df(engine, daily_sql, {"ts_code": ts_code})
    dividend_df = query_df(engine, dividend_sql, {"ts_code": ts_code})
    audit_df = query_df(engine, audit_sql, {"ts_code": ts_code})

    if income_df.empty or balance_df.empty or cash_df.empty or indicator_df.empty or daily_df.empty:
        print(f"{ts_code} 的核心财务数据不完整，无法生成报告。")
        sys.exit(1)

    annual_df = build_annual_table(income_df, balance_df, cash_df, indicator_df)
    quarter = build_quarter_snapshot(income_df, balance_df, cash_df, indicator_df)
    dividend_lines = summarize_dividend(dividend_df)
    audit_lines = summarize_audit(audit_df)
    report = build_report(
        ts_code=ts_code,
        stock_row=stock_df.iloc[0],
        daily_row=daily_df.iloc[0],
        annual_df=annual_df,
        quarter=quarter,
        dividend_lines=dividend_lines,
        audit_lines=audit_lines,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{ts_code.replace('.', '-')}-report.md"
    output_path.write_text(report, encoding="utf-8")

    print(f"报告已生成: {output_path}")
    print(report)


if __name__ == "__main__":
    main()
