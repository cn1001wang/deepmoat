import os
import sys
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
)
DB_URL = DATABASE_URL.replace("+psycopg2", "")
engine = create_engine(DB_URL)


_NON_STD_EXPLICIT = ["否定意见", "无法表示意见", "拒绝表示意见"]


@dataclass
class IndicatorRecord:
    end_date: str
    roe: Optional[float]
    gross_margin: Optional[float]
    current_ratio: Optional[float]
    debt_to_assets: Optional[float]
    net_cash_ratio: Optional[float]
    audit_result: Optional[str] = None
    audit_agency: Optional[str] = None


def fetch_stock_name(ts_code: str) -> (str, str):
    query = text(
        "SELECT name, industry FROM stock_basic WHERE ts_code = :ts_code LIMIT 1"
    )
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"ts_code": ts_code}).first()
    except SQLAlchemyError as exc:
        raise RuntimeError(f"查询公司信息失败：{exc}")

    if result is None:
        raise ValueError(f"未找到股票代码 {ts_code} 的基本信息。")

    return result[0], result[1] or ""


def load_audit_opinions(ts_code: str) -> pd.DataFrame:
    query = text(
        "SELECT end_date, audit_result, audit_agency "
        "FROM fina_audit WHERE ts_code = :ts_code "
        "ORDER BY end_date DESC LIMIT 20"
    )
    try:
        return pd.read_sql(query, engine, params={"ts_code": ts_code})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"读取审计意见失败：{exc}")


def load_net_cash_ratio(ts_code: str) -> pd.DataFrame:
    query = text(
        "SELECT end_date, ocf_to_profit "
        "FROM fina_indicator WHERE ts_code = :ts_code "
        "ORDER BY end_date DESC LIMIT 20"
    )
    try:
        return pd.read_sql(query, engine, params={"ts_code": ts_code})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"读取净现比指标失败：{exc}")


def load_recent_indicators(ts_code: str) -> pd.DataFrame:
    query = text(
        "SELECT end_date, roe, grossprofit_margin AS gross_margin, current_ratio, debt_to_assets "
        "FROM fina_indicator WHERE ts_code = :ts_code "
        "ORDER BY end_date DESC LIMIT 40"
    )
    try:
        return pd.read_sql(query, engine, params={"ts_code": ts_code})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"读取财务指标失败：{exc}")


def select_ten_years(df: pd.DataFrame) -> pd.DataFrame:
    df_yearly = df[df["end_date"].str.endswith("1231")].copy()
    df_yearly["year"] = df_yearly["end_date"].str[:4]
    df_yearly = df_yearly.drop_duplicates(subset=["year"]).sort_values("end_date", ascending=False)
    return df_yearly.head(10)


def select_latest_quarter(df: pd.DataFrame) -> pd.Series:
    return df.iloc[0]


def aggregate_records(
    df_indicators: pd.DataFrame,
    df_cash: pd.DataFrame,
    df_audit: pd.DataFrame,
) -> List[IndicatorRecord]:
    df = df_indicators.drop_duplicates(subset=["end_date"]).sort_values("end_date", ascending=False)
    cash_map = {
        row["end_date"]: row["ocf_to_profit"]
        for _, row in df_cash.iterrows()
        if pd.notna(row.get("ocf_to_profit"))
    }
    audit_map = {
        row["end_date"]: (row.get("audit_result"), row.get("audit_agency"))
        for _, row in df_audit.iterrows()
        if pd.notna(row.get("audit_result"))
    }

    records: List[IndicatorRecord] = []
    for _, row in df.iterrows():
        end_date = row["end_date"]
        audit_result, audit_agency = audit_map.get(end_date, (None, None))
        records.append(
            IndicatorRecord(
                end_date=end_date,
                roe=float(row["roe"]) if pd.notna(row["roe"]) else None,
                gross_margin=float(row["gross_margin"]) if pd.notna(row["gross_margin"]) else None,
                current_ratio=float(row["current_ratio"]) if pd.notna(row["current_ratio"]) else None,
                debt_to_assets=float(row["debt_to_assets"]) if pd.notna(row["debt_to_assets"]) else None,
                net_cash_ratio=float(cash_map[end_date]) if cash_map.get(end_date) else None,
                audit_result=audit_result,
                audit_agency=audit_agency,
            )
        )
    return records


def is_non_standard_audit(audit_result: Optional[str]) -> bool:
    """
    非标准意见：否定、无法表示、保留意见（需排除"无保留意见"/"标准无保留意见"）
    """
    if not audit_result:
        return False
    if any(kw in audit_result for kw in _NON_STD_EXPLICIT):
        return True
    # "保留意见" 非标，但 "无保留意见" / "标准无保留意见" 是标准意见
    if "保留意见" in audit_result and "无保留意见" not in audit_result:
        return True
    return False


def check_one_vote(records: List[IndicatorRecord]) -> (bool, List[str]):
    reasons: List[str] = []
    net_cash = [rec.net_cash_ratio for rec in records if rec.net_cash_ratio is not None]
    if len(net_cash) >= 3 and all(val < 0.7 for val in net_cash[:3]):
        reasons.append("连续3年净现比 < 0.7")

    high_debt = [rec for rec in records if rec.debt_to_assets is not None and rec.debt_to_assets > 80]
    if high_debt:
        reasons.append("资产负债率 > 80%")

    non_std = [rec for rec in records if is_non_standard_audit(rec.audit_result)]
    if non_std:
        for rec in non_std:
            reasons.append(f"非标审计意见（{rec.end_date[:4]}年）：{rec.audit_result}")
    elif all(rec.audit_result is None for rec in records):
        reasons.append("审计意见：数据缺失，已忽略")

    return len(reasons) > 0, reasons


def check_core_conditions(records: List[IndicatorRecord]) -> bool:
    if len(records) < 5:
        return False
    top10 = records[:10]
    return all(
        (rec.roe or 0) > 15
        and (rec.gross_margin or 0) > 20
        and (rec.current_ratio or 0) > 1.5
        for rec in top10
    )


def format_trend(records: List[IndicatorRecord], attr: str) -> str:
    trend = []
    for rec in records[:10]:
        val = getattr(rec, attr)
        if val is None:
            trend.append(f"{rec.end_date}: N/A")
        else:
            trend.append(f"{rec.end_date}: {val:.2f}%")
    return " | ".join(trend) if trend else "无数据"


def main():
    if len(sys.argv) < 2:
        print("请在命令行指定股票代码（如 600519.SH）。")
        sys.exit(1)

    ts_code = sys.argv[1].strip()
    try:
        name, industry = fetch_stock_name(ts_code)
    except Exception as exc:
        print(f"获取公司信息失败：{exc}")
        sys.exit(1)

    df_recent = load_recent_indicators(ts_code)
    if df_recent.empty:
        print("未查到财务指标数据，无法分析。")
        return

    latest_quarter = select_latest_quarter(df_recent)
    df_ten_years = select_ten_years(df_recent)
    if df_ten_years.empty:
        print("未查到十年年报数据，无法分析。")
        return

    df_cash = load_net_cash_ratio(ts_code)
    df_audit = load_audit_opinions(ts_code)
    records = aggregate_records(df_ten_years, df_cash, df_audit)

    abnormal, abnormal_reasons = check_one_vote(records)
    core_met = check_core_conditions(records)

    conclusion = (
        "不合格，需警惕" if abnormal else "符合关注标准" if core_met else "一般，需进一步分析"
    )

    print("\n=== 基础判断报告 ===")
    print(f"公司：{name} ({ts_code})")
    print(f"行业：{industry or '未知'}")

    print("\n最新季度表现：")
    print(f"报告期：{latest_quarter['end_date']}")
    print(
        f"ROE：{latest_quarter['roe']:.2f}%" if pd.notna(latest_quarter['roe']) else "ROE：N/A"
    )
    print(
        f"毛利率：{latest_quarter['gross_margin']:.2f}%" if pd.notna(latest_quarter['gross_margin']) else "毛利率：N/A"
    )
    print(
        f"流动比率：{latest_quarter['current_ratio']:.2f}" if pd.notna(latest_quarter['current_ratio']) else "流动比率：N/A"
    )
    print(
        f"资产负债率：{latest_quarter['debt_to_assets']:.2f}%" if pd.notna(latest_quarter['debt_to_assets']) else "资产负债率：N/A"
    )

    print("\n最近十年趋势：")
    print("ROE：" + format_trend(records, "roe"))
    print("毛利率：" + format_trend(records, "gross_margin"))
    print("资产负债率：" + format_trend(records, "debt_to_assets"))

    print("\n年度审计意见：")
    has_audit = False
    for rec in records:
        if rec.audit_result:
            has_audit = True
            flag = "[!] " if is_non_standard_audit(rec.audit_result) else "[ok] "
            agency = f"  [{rec.audit_agency}]" if rec.audit_agency else ""
            print(f"  {flag}{rec.end_date[:4]}年：{rec.audit_result}{agency}")
    if not has_audit:
        print("  暂无审计意见数据")

    print("\n异常信号")
    print("有" if abnormal else "无")
    if abnormal_reasons:
        for reason in abnormal_reasons:
            print(f" - {reason}")

    print("\n结论：" + conclusion)

    print("\n主要风险点：")
    if abnormal:
        print(" - 存在一票否决项，需重点关注财务健康。")
    else:
        print(" - 资产负债率与现金回收需持续监测。")

    print("\n优点：")
    if core_met:
        print(" - ROE、毛利率、流动性均满足高质量企业标准。")
    else:
        print(" - ROE 与毛利率尚具备一定优势，可继续观察。")


if __name__ == "__main__":
    main()
