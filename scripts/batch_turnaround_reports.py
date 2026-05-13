#!/usr/bin/env python3
"""
按“困境反转”视角批量生成三类报告：
1) r12
2) analysis
3) value

实现方式：
- 复用 scripts/batch_generate_all_reports.py 的生成能力
- 对每份报告追加“困境反转专项判断”段落（事实/计算结果/推断）
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "outputs" / "reports"
BASE_SCRIPT = ROOT / "scripts" / "batch_generate_all_reports.py"


TARGET_NAMES = [
    "东方盛虹",
    "恒逸石化",
    "华润微",
    "长源电力",
    "三峡水利",
    "南方航空",
    "天齐锂业",
    "中孚实业",
]


def load_base_module():
    spec = importlib.util.spec_from_file_location("batch_base", BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["batch_base"] = module
    spec.loader.exec_module(module)
    return module


def fmt_num(v):
    if v is None or pd.isna(v):
        return "N/A"
    return f"{float(v):.2f}"


def fmt_pct(v):
    if v is None or pd.isna(v):
        return "N/A"
    return f"{float(v):.2f}%"


def calc_growth(cur, prev):
    if cur is None or prev is None or pd.isna(cur) or pd.isna(prev) or not prev:
        return None
    return (float(cur) - float(prev)) / abs(float(prev)) * 100


def fetch_turnaround_metrics(engine, ts_code: str) -> dict:
    income = pd.read_sql(
        text(
            """
            SELECT end_date, total_revenue, n_income_attr_p
            FROM income
            WHERE ts_code=:ts_code AND report_type='1'
            ORDER BY end_date DESC
            """
        ),
        engine,
        params={"ts_code": ts_code},
    )
    balance = pd.read_sql(
        text(
            """
            SELECT end_date, total_assets, total_liab
            FROM balancesheet
            WHERE ts_code=:ts_code AND report_type='1'
            ORDER BY end_date DESC
            """
        ),
        engine,
        params={"ts_code": ts_code},
    )
    cash = pd.read_sql(
        text(
            """
            SELECT end_date, n_cashflow_act, free_cashflow
            FROM cashflow
            WHERE ts_code=:ts_code AND report_type='1'
            ORDER BY end_date DESC
            """
        ),
        engine,
        params={"ts_code": ts_code},
    )
    daily = pd.read_sql(
        text(
            """
            SELECT trade_date, close, pe_ttm, pb, ps_ttm, dv_ttm
            FROM daily_basic
            WHERE ts_code=:ts_code
            ORDER BY trade_date DESC
            LIMIT 1
            """
        ),
        engine,
        params={"ts_code": ts_code},
    )

    latest_income = income.iloc[0] if not income.empty else None
    prev_income = income.iloc[1] if len(income) >= 2 else None
    latest_balance = balance.iloc[0] if not balance.empty else None
    prev_balance = balance.iloc[1] if len(balance) >= 2 else None
    latest_cash = cash.iloc[0] if not cash.empty else None
    prev_cash = cash.iloc[1] if len(cash) >= 2 else None
    latest_daily = daily.iloc[0] if not daily.empty else None

    revenue_yoy = (
        calc_growth(latest_income["total_revenue"], prev_income["total_revenue"])
        if latest_income is not None and prev_income is not None
        else None
    )
    profit_yoy = (
        calc_growth(latest_income["n_income_attr_p"], prev_income["n_income_attr_p"])
        if latest_income is not None and prev_income is not None
        else None
    )
    cfo_yoy = (
        calc_growth(latest_cash["n_cashflow_act"], prev_cash["n_cashflow_act"])
        if latest_cash is not None and prev_cash is not None
        else None
    )

    debt_ratio_latest = None
    debt_ratio_prev = None
    if latest_balance is not None and latest_balance["total_assets"]:
        debt_ratio_latest = float(latest_balance["total_liab"]) / float(latest_balance["total_assets"]) * 100
    if prev_balance is not None and prev_balance["total_assets"]:
        debt_ratio_prev = float(prev_balance["total_liab"]) / float(prev_balance["total_assets"]) * 100

    # 反转信号粗分：盈利改善、现金流改善、杠杆改善满足 2/3 即可视为“反转进行中”
    score = 0
    if profit_yoy is not None and profit_yoy > 0:
        score += 1
    if cfo_yoy is not None and cfo_yoy > 0:
        score += 1
    if (
        debt_ratio_latest is not None
        and debt_ratio_prev is not None
        and debt_ratio_latest < debt_ratio_prev
    ):
        score += 1

    label = "反转进行中" if score >= 2 else "反转待确认"

    return {
        "latest_end_date": latest_income["end_date"] if latest_income is not None else "数据缺失/待核实",
        "price_date": latest_daily["trade_date"] if latest_daily is not None else "数据缺失/待核实",
        "close": latest_daily["close"] if latest_daily is not None else None,
        "pe_ttm": latest_daily["pe_ttm"] if latest_daily is not None else None,
        "pb": latest_daily["pb"] if latest_daily is not None else None,
        "revenue_yoy": revenue_yoy,
        "profit_yoy": profit_yoy,
        "cfo_yoy": cfo_yoy,
        "debt_ratio_latest": debt_ratio_latest,
        "debt_ratio_prev": debt_ratio_prev,
        "turnaround_score": score,
        "turnaround_label": label,
    }


def turnaround_section(name: str, ts_code: str, m: dict) -> str:
    return f"""
## 困境反转专项判断（{name}）
事实：
- 价格日期：{m["price_date"]}；财报日期：{m["latest_end_date"]}。
- 当前收盘价 {fmt_num(m["close"])} 元，PE(TTM) {fmt_num(m["pe_ttm"])}，PB {fmt_num(m["pb"])}。
计算结果：
- 营收同比 {fmt_pct(m["revenue_yoy"])}，净利润同比 {fmt_pct(m["profit_yoy"])}，经营现金流同比 {fmt_pct(m["cfo_yoy"])}。
- 资产负债率：最新 {fmt_pct(m["debt_ratio_latest"])}，上期 {fmt_pct(m["debt_ratio_prev"])}。
- 困境反转评分：{m["turnaround_score"]}/3，状态：{m["turnaround_label"]}。
推断：
- 若“盈利修复 + 现金流修复 + 杠杆缓解”连续两个报告期维持，则反转概率提升；若任一项再度恶化，应下调反转置信度。
"""


def append_section(report_path: Path, section: str):
    if not report_path.exists():
        return
    original = report_path.read_text(encoding="utf-8")
    if "## 困境反转专项判断" in original:
        return
    report_path.write_text(original.rstrip() + "\n\n" + section.strip() + "\n", encoding="utf-8")


def main():
    base = load_base_module()
    base.TARGET_NAMES = TARGET_NAMES

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    engine = base.load_engine()
    run_timestamp = base.short_ts()
    targets, unresolved = base.resolve_targets(engine)

    results = []
    for idx, t in enumerate(targets, start=1):
        print(f"[{idx}/{len(targets)}] Processing: {t.query_name} ({t.ts_code or t.symbol})")
        row = {
            "name": t.display_name,
            "symbol": t.symbol,
            "source": t.source,
            "status": "ok",
            "error": "",
        }

        metrics = fetch_turnaround_metrics(engine, t.ts_code) if t.ts_code else {
            "latest_end_date": "数据缺失/待核实",
            "price_date": "数据缺失/待核实",
            "close": None,
            "pe_ttm": None,
            "pb": None,
            "revenue_yoy": None,
            "profit_yoy": None,
            "cfo_yoy": None,
            "debt_ratio_latest": None,
            "debt_ratio_prev": None,
            "turnaround_score": 0,
            "turnaround_label": "反转待确认",
        }

        try:
            r12 = base.build_r12_local(engine, t, run_timestamp)
            append_section(r12, turnaround_section(t.display_name, t.ts_code or t.symbol, metrics))
            row["r12"] = str(r12.relative_to(ROOT))
        except Exception as exc:
            row["status"] = "partial_failed"
            row["error"] = f"r12_failed: {exc}"
            row["r12"] = ""

        analysis_path, analysis_err = base.run_analysis(t)
        if analysis_path:
            append_section(analysis_path, turnaround_section(t.display_name, t.ts_code or t.symbol, metrics))
            row["analysis"] = str(analysis_path.relative_to(ROOT))
        else:
            row["analysis"] = ""
            row["status"] = "partial_failed"
            row["error"] = (row["error"] + " | " if row["error"] else "") + (analysis_err or "analysis_failed")

        value_final, value_draft, value_err = base.run_value(t)
        if value_final:
            append_section(value_final, turnaround_section(t.display_name, t.ts_code or t.symbol, metrics))
            row["value"] = str(value_final.relative_to(ROOT))
        else:
            row["value"] = ""
            row["status"] = "partial_failed"
            row["error"] = (row["error"] + " | " if row["error"] else "") + (value_err or "value_failed")
        if value_draft:
            row["value_draft"] = str(value_draft.relative_to(ROOT))

        results.append(row)

    idx_path = REPORT_ROOT / f"index_turnaround_{datetime.now().strftime('%y%m%d%H%M')}.md"
    lines = [
        "# 困境反转批量报告索引",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 总标的数：{len(results)}",
        f"- 全成功：{sum(1 for r in results if r['status']=='ok')}",
        "",
        "| 标的 | 代码 | r12 | analysis | value | 状态 | 错误 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['symbol']} | {r.get('r12','')} | {r.get('analysis','')} | {r.get('value','')} | {r['status']} | {r.get('error','')} |"
        )
    if unresolved:
        lines.extend(["", "## 未命中标的", ""])
        for u in unresolved:
            lines.append(f"- {u['name']}: {u['reason']}")

    idx_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Batch completed. Index: {idx_path}")


if __name__ == "__main__":
    main()
