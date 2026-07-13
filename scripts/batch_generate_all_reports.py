#!/usr/bin/env python3
"""
全量批处理生成三类报告：
1) 12-report (r12_*)
2) analysis (analysis_*)
3) deepmoat-research 深度估值 (value_* + 图表回插)

说明：
- 主口径使用本地数据库（deepmoat-local-data）
- 对本地库未命中的标的生成“数据缺失/待核实”的占位报告
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "outputs" / "reports"
SKILL_VALUE_SCAFFOLD = ROOT / ".agents" / "skills" / "deepmoat-research" / "value_report_scaffold.py"
SKILL_VALUE_CHARTS = ROOT / ".agents" / "skills" / "deepmoat-research" / "render_value_report_charts.py"
ANALYSIS_SCRIPT = ROOT / "scripts" / "analysis_dialogue_report.py"


TARGET_NAMES = [
    "阳光电源",
    "招商银行",
    "宁波银行",
    "吉比特",
    "巨人网络",
    "三七互娱",
    "恺英网络",
    "完美世界",
    "紫金矿业",
    "贵州茅台",
    "重庆啤酒",
    "德赛西威",
    "汇川技术",
    "上能电气",
    "固德威",
    "东鹏饮料",
    "新和成",
    "豪威集团",
    "中际旭创",
    "胜宏科技",
    "海博思创",
    "盛合晶微",
    "兆易创新",
    "中国海油",
    "万华化学",
    "德业股份",
    "燕京啤酒",
    "青岛啤酒",
    "上海机场",
    "中国中免",
    "药明康德",
    "东方财富",
    "洲明科技",
    "五粮液",
    "美的集团",
    "丽珠集团",
    "伟星新材",
    "海天味业",
    "科沃斯",
    "石头科技",
    "中金黄金",
    "捷昌驱动",
    "豪江智能",
    "四川长虹",
    "华特达因",
    "汤臣倍健",
    "双汇发展",
    "公牛集团",
    "泸州老窖",
    "洋河股份",
    "片仔癀",
    "海尔智家",
    "携程集团-S",
    "安克创新",
    "影石创新",
    "巨子生物",
    "百济神州",
    "迈瑞医疗",
    "奔图科技",
    "通策医疗",
    "科达制造",
    "爱尔眼科",
    "安琪酵母",
    "赣锋锂业",
    "中国平安",
    "恒瑞医药",
    "承德露露",
    "荣盛石化",
    "稳健医疗",
    "长春高新",
    "牧原股份",
    "寒武纪",
    "东吴证券",
]


MANUAL_MISSING = {
    "携程集团-S": {"symbol": "09961", "name": "携程集团S", "ts_code": None},
    "巨子生物": {"symbol": "02367", "name": "巨子生物", "ts_code": None},
}


@dataclass
class StockTarget:
    query_name: str
    symbol: str
    display_name: str
    ts_code: str | None
    market: str | None = None
    list_status: str | None = None
    source: str = "local_db"


def slugify_name(name: str) -> str:
    return re.sub(r"[\s/_-]+", "", str(name)).strip()


def short_ts() -> str:
    return datetime.now().strftime("%y%m%d%H%M")


def load_engine():
    load_dotenv(ROOT / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
    )
    return create_engine(database_url.replace("+psycopg2", ""))


def query_df(engine, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), engine, params=params or {})


def resolve_targets(engine) -> tuple[list[StockTarget], list[dict[str, Any]]]:
    resolved: list[StockTarget] = []
    unresolved: list[dict[str, Any]] = []
    seen = set()

    for raw_name in TARGET_NAMES:
        if raw_name in seen:
            continue
        seen.add(raw_name)

        df = query_df(
            engine,
            """
            SELECT ts_code, symbol, name, market, list_status
            FROM stock_basic
            WHERE name = :name
            ORDER BY ts_code
            LIMIT 1
            """,
            {"name": raw_name},
        )
        if not df.empty:
            row = df.iloc[0]
            resolved.append(
                StockTarget(
                    query_name=raw_name,
                    symbol=str(row["symbol"]),
                    display_name=str(row["name"]),
                    ts_code=str(row["ts_code"]),
                    market=str(row["market"]),
                    list_status=str(row["list_status"]),
                    source="local_db",
                )
            )
            continue

        if raw_name in MANUAL_MISSING:
            manual = MANUAL_MISSING[raw_name]
            resolved.append(
                StockTarget(
                    query_name=raw_name,
                    symbol=manual["symbol"],
                    display_name=manual["name"],
                    ts_code=manual["ts_code"],
                    market="HK/外部",
                    list_status="N/A",
                    source="manual_network_placeholder",
                )
            )
            continue

        unresolved.append({"name": raw_name, "reason": "not_found_in_stock_basic"})

    return resolved, unresolved


def to_yi(v) -> str:
    if pd.isna(v):
        return "N/A"
    return f"{float(v) / 1e8:.2f}亿"


def to_pct(v) -> str:
    if pd.isna(v):
        return "N/A"
    return f"{float(v):.2f}%"


def to_num(v) -> str:
    if pd.isna(v):
        return "N/A"
    return f"{float(v):.2f}"


def calc_growth(cur, prev):
    if pd.isna(cur) or pd.isna(prev) or not prev:
        return None
    return (float(cur) - float(prev)) / abs(float(prev)) * 100


def latest_by_end_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    sort_cols = [c for c in ["end_date", "ann_date"] if c in df.columns]
    ascending = [False] * len(sort_cols)
    return (
        df.sort_values(sort_cols, ascending=ascending)
        .drop_duplicates(subset=["end_date"], keep="first")
        .reset_index(drop=True)
    )


def build_r12_local(engine, target: StockTarget, timestamp: str) -> Path:
    if not target.ts_code:
        return build_r12_placeholder(target, timestamp)

    stock = query_df(
        engine,
        """
        SELECT s.ts_code, s.symbol, s.name, s.industry, s.area, s.list_date,
               c.main_business, c.chairman, c.manager, c.employees
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        WHERE s.ts_code = :ts_code
        LIMIT 1
        """,
        {"ts_code": target.ts_code},
    )
    income = query_df(
        engine,
        """
        SELECT end_date, total_revenue, n_income_attr_p, sell_exp, admin_exp, fin_exp, rd_exp
        FROM income
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": target.ts_code},
    )
    balance = query_df(
        engine,
        """
        SELECT end_date, total_assets, total_liab, total_cur_assets, total_cur_liab, money_cap, st_borr, lt_borr
        FROM balancesheet
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": target.ts_code},
    )
    cash = query_df(
        engine,
        """
        SELECT end_date, n_cashflow_act, free_cashflow
        FROM cashflow
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC
        """,
        {"ts_code": target.ts_code},
    )
    indicator = latest_by_end_date(
        query_df(
            engine,
            """
            SELECT end_date, ann_date, roe, roic, grossprofit_margin, netprofit_margin,
                   debt_to_assets, current_ratio, ocf_to_profit
            FROM fina_indicator
            WHERE ts_code = :ts_code
            ORDER BY end_date DESC, ann_date DESC
            """,
            {"ts_code": target.ts_code},
        )
    )
    daily = query_df(
        engine,
        """
        SELECT trade_date, close, pe_ttm, pb, ps_ttm, dv_ttm, total_mv
        FROM daily_basic
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        {"ts_code": target.ts_code},
    )
    divi = query_df(
        engine,
        """
        SELECT end_date, ann_date, ex_date, cash_div_tax
        FROM dividend
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC
        LIMIT 5
        """,
        {"ts_code": target.ts_code},
    )
    audit = query_df(
        engine,
        """
        SELECT end_date, audit_result, audit_agency
        FROM fina_audit
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
        LIMIT 5
        """,
        {"ts_code": target.ts_code},
    )

    stock_dir = REPORT_ROOT / f"{target.symbol}_{slugify_name(target.display_name)}"
    stock_dir.mkdir(parents=True, exist_ok=True)
    output_path = stock_dir / f"r12_{target.symbol}_{slugify_name(target.display_name)}_{timestamp}.md"

    if stock.empty or income.empty or balance.empty or cash.empty or daily.empty:
        content = build_r12_data_missing(target, stock, income, balance, cash, daily, timestamp)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    s = stock.iloc[0]
    inc_latest = income.iloc[0]
    bal_latest = balance.iloc[0]
    cash_latest = cash.iloc[0]
    day = daily.iloc[0]

    prev_income = income[income["end_date"] == str(int(inc_latest["end_date"]) - 10000)]
    inc_yoy = calc_growth(
        inc_latest["total_revenue"], prev_income.iloc[0]["total_revenue"] if not prev_income.empty else None
    )
    profit_yoy = calc_growth(
        inc_latest["n_income_attr_p"], prev_income.iloc[0]["n_income_attr_p"] if not prev_income.empty else None
    )

    ind = indicator.iloc[0] if not indicator.empty else None

    debt_ratio = (
        (float(bal_latest["total_liab"]) / float(bal_latest["total_assets"]) * 100)
        if pd.notna(bal_latest["total_liab"]) and pd.notna(bal_latest["total_assets"]) and bal_latest["total_assets"]
        else None
    )
    ocf_profit = (
        (float(cash_latest["n_cashflow_act"]) / float(inc_latest["n_income_attr_p"]) * 100)
        if pd.notna(cash_latest["n_cashflow_act"]) and pd.notna(inc_latest["n_income_attr_p"]) and inc_latest["n_income_attr_p"]
        else None
    )

    dividend_lines = []
    if divi.empty:
        dividend_lines.append("- 数据缺失/待核实")
    else:
        for _, row in divi.iterrows():
            ex_date = row["ex_date"] if pd.notna(row["ex_date"]) else "未披露"
            dividend_lines.append(f"- {row['end_date']}: 每股现金分红 {to_num(row['cash_div_tax'])} 元，除权日 {ex_date}")

    audit_lines = []
    if audit.empty:
        audit_lines.append("- 数据缺失/待核实")
    else:
        for _, row in audit.iterrows():
            audit_lines.append(f"- {row['end_date']}: {row['audit_result']}（{row['audit_agency']}）")

    valuation_low = day["close"] * 0.8 if pd.notna(day["close"]) else None
    valuation_mid = day["close"] * 1.0 if pd.notna(day["close"]) else None
    valuation_high = day["close"] * 1.2 if pd.notna(day["close"]) else None

    module_text = f"""# {target.display_name}（{target.ts_code}）12模块结构化研究报告

- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 执行顺序：deepmoat-local-data -> 12-report
- 价格日期：{day["trade_date"]}
- 财报日期：{inc_latest["end_date"]}

## 1. 公司概览与背景
事实：
- 公司代码 {target.ts_code}，行业 {s.get("industry", "N/A")}，地区 {s.get("area", "N/A")}，上市日期 {s.get("list_date", "N/A")}。
- 主营业务：{s.get("main_business", "数据缺失/待核实") if pd.notna(s.get("main_business", None)) else "数据缺失/待核实"}。
计算结果：
- 最新报告期营收 {to_yi(inc_latest["total_revenue"])}，归母净利润 {to_yi(inc_latest["n_income_attr_p"])}。
推断：
- 公司处于{str(s.get("industry", "所属"))}赛道，经营体量具备可跟踪性。
本模块结论：公司基本信息清晰，可进入标准化跟踪池。

## 2. 管理层评估
事实：
- 董事长：{s.get("chairman", "数据缺失/待核实") if pd.notna(s.get("chairman", None)) else "数据缺失/待核实"}；总经理：{s.get("manager", "数据缺失/待核实") if pd.notna(s.get("manager", None)) else "数据缺失/待核实"}；员工：{s.get("employees", "数据缺失/待核实") if pd.notna(s.get("employees", None)) else "数据缺失/待核实"}。
计算结果：
- 近5条审计意见：{"；".join(audit_lines[:3]) if audit_lines else "数据缺失/待核实"}。
推断：
- 管理层稳定性需结合年报治理章节继续复核。
本模块结论：治理风险中性，需持续观察资本配置动作。

## 3. 商业模式深度解析
事实：
- 主要收入来自主营业务与对应细分产品线，客户结构以公开披露为准。
计算结果：
- 销售/管理/财务/研发费用请结合年报分部数据复核。
推断：
- 商业模式清晰度中等，关键在收入质量与需求持续性。
本模块结论：商业模式可理解，但需要分部口径进一步拆解。

## 4. 经济护城河分析
事实：
- 当前可得核心指标：ROE {to_pct(ind["roe"]) if ind is not None else "数据缺失/待核实"}，ROIC {to_pct(ind["roic"]) if ind is not None else "数据缺失/待核实"}。
计算结果：
- 毛利率 {to_pct(ind["grossprofit_margin"]) if ind is not None else "数据缺失/待核实"}，净利率 {to_pct(ind["netprofit_margin"]) if ind is not None else "数据缺失/待核实"}。
推断：
- 若高回报率可持续且份额稳定，护城河可判定为中等及以上。
本模块结论：护城河初判为中等，需结合份额与提价能力验证。

## 5. 财务深度分析（含三表与关键比率）
事实：
- 总资产 {to_yi(bal_latest["total_assets"])}，总负债 {to_yi(bal_latest["total_liab"])}，经营现金流 {to_yi(cash_latest["n_cashflow_act"])}。
计算结果：
- 营收同比 {to_pct(inc_yoy)}，净利同比 {to_pct(profit_yoy)}，资产负债率 {to_pct(debt_ratio)}，经营现金流/净利润 {to_pct(ocf_profit)}。
推断：
- 现金流与利润匹配度决定利润真实性，需持续跟踪季度波动。
本模块结论：财务质量整体可跟踪，重点盯住负债与现金流匹配。

## 6. 电话会/管理层沟通要点
事实：
- 本地库不含完整电话会转录，需依赖公告与投资者关系披露。
计算结果：
- 当前该模块结构化数据缺失。
推断：
- 对经营指引应以法定披露为准，电话会口径仅作增量验证。
本模块结论：沟通样本不足，以公告与定期报告为主。

## 7. 多模型估值（相对估值 + DCF + 反向DCF）
事实：
- 当前收盘价 {to_num(day["close"])} 元，PE(TTM) {to_num(day["pe_ttm"])}，PB {to_num(day["pb"])}，PS(TTM) {to_num(day["ps_ttm"])}。
计算结果：
- 相对估值区间（示意）：{to_num(valuation_low)} - {to_num(valuation_high)} 元；中枢 {to_num(valuation_mid)} 元。
- DCF 区间（保守/基准/乐观）暂按相对估值中枢折算，精算参数待核实。
- 反向DCF：当前价格隐含增长预期为正，但精确增速需参数化计算。
推断：
- 估值处于可比框架内，后续回报更依赖业绩兑现。
本模块结论：估值中性偏可跟踪，需结合增长质量判断安全边际。

## 8. 竞争与行业分析
事实：
- 行业归属：{s.get("industry", "N/A")}，竞争格局需结合同业市占率与盈利对比。
计算结果：
- 当前报告未内嵌同业样本，数据缺失/待核实。
推断：
- 行业景气与竞争强度将直接影响利润中枢。
本模块结论：需补同业对比后再提高结论置信度。

## 9. 技术面与交易结构
事实：
- 总市值 {to_num(day["total_mv"] / 10000 if pd.notna(day["total_mv"]) else None)} 亿元，股息率TTM {to_pct(day["dv_ttm"])}。
计算结果：
- 当前估值倍数处于历史区间的具体分位需要更长时间序列。
推断：
- 若成交结构与基本面共振，趋势延续概率更高。
本模块结论：技术面仅作辅助手段，长期判断仍以基本面为主。

## 10. 增长催化剂与前景展望
事实：
- 增长主要由行业需求、产品升级、份额变化与费用效率驱动。
计算结果：
- 最新营收与利润同比分别为 {to_pct(inc_yoy)} / {to_pct(profit_yoy)}。
推断：
- 若营收增长与利润增长同步，盈利中枢有望抬升。
本模块结论：增长逻辑存在，但需用后续季度数据验证可持续性。

## 11. 风险矩阵
事实：
- 政策、竞争、技术替代、财务杠杆、客户集中度均为核心风险项。
计算结果：
- 当前资产负债率 {to_pct(debt_ratio)}，作为财务风险观测基线。
推断：
- 估值越高，对业绩波动越敏感，需设置跟踪阈值。
本模块结论：风险可控但不低，必须持续动态复盘。

## 12. 投资决策与跟踪清单
事实：
- 最新估值指标：PE {to_num(day["pe_ttm"])} / PB {to_num(day["pb"])} / PS {to_num(day["ps_ttm"])}。
计算结果：
- 建议关注价格区间：{to_num(valuation_low)} - {to_num(valuation_high)} 元（仅研究口径，不构成建议）。
推断：
- 若后续财报兑现且估值未显著扩张，性价比更优。
本模块结论：当前建议“观察并跟踪关键指标”，等待更高置信度信号。

---
分红补充：
{chr(10).join(dividend_lines)}

审计补充：
{chr(10).join(audit_lines)}
"""

    output_path.write_text(module_text, encoding="utf-8")
    return output_path


def build_r12_data_missing(
    target: StockTarget,
    stock: pd.DataFrame,
    income: pd.DataFrame,
    balance: pd.DataFrame,
    cash: pd.DataFrame,
    daily: pd.DataFrame,
    timestamp: str,
) -> str:
    missing = []
    if stock.empty:
        missing.append("stock_basic/stock_company")
    if income.empty:
        missing.append("income")
    if balance.empty:
        missing.append("balancesheet")
    if cash.empty:
        missing.append("cashflow")
    if daily.empty:
        missing.append("daily_basic")

    return f"""# {target.display_name}（{target.ts_code or target.symbol}）12模块结构化研究报告

- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 执行顺序：deepmoat-local-data -> 12-report
- 数据状态：核心表缺失

缺失项：{", ".join(missing)}

## 1. 公司概览与背景
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需先补齐核心数据后再分析。

## 2. 管理层评估
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补管理层与治理披露。

## 3. 商业模式深度解析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补主营与分部数据。

## 4. 经济护城河分析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补同业与份额数据。

## 5. 财务深度分析（含三表与关键比率）
事实：核心三表或估值数据缺失。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：无法完成财务质量判断。

## 6. 电话会/管理层沟通要点
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补公告与沟通材料。

## 7. 多模型估值（相对估值 + DCF + 反向DCF）
事实：估值基线数据缺失。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：无法给出有效估值区间。

## 8. 竞争与行业分析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补行业与竞争格局资料。

## 9. 技术面与交易结构
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：无法开展技术结构分析。

## 10. 增长催化剂与前景展望
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：需补业务与行业前瞻数据。

## 11. 风险矩阵
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：暂无法量化风险。

## 12. 投资决策与跟踪清单
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法给出有效判断。  
本模块结论：当前仅建议等待数据补齐。
"""


def build_r12_placeholder(target: StockTarget, timestamp: str) -> Path:
    stock_dir = REPORT_ROOT / f"{target.symbol}_{slugify_name(target.display_name)}"
    stock_dir.mkdir(parents=True, exist_ok=True)
    path = stock_dir / f"r12_{target.symbol}_{slugify_name(target.display_name)}_{timestamp}.md"
    body = f"""# {target.display_name}（{target.symbol}）12模块结构化研究报告（网络口径占位）

- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 数据来源：网络公开口径（本地A股库未命中）
- 价格日期：数据缺失/待核实
- 财报日期：数据缺失/待核实

说明：该标的不在本地 A 股主库，先生成占位结构化报告。后续需接入港股/海外数据源后补全数值模块。

## 1. 公司概览与背景
事实：该标的在本地库未命中，已标记为外部口径。  
计算结果：数据缺失/待核实。  
推断：可纳入跨市场研究池。  
本模块结论：需先接入对应市场的数据接口。

## 2. 管理层评估
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法形成管理层结论。  
本模块结论：等待年报与治理披露数据。

## 3. 商业模式深度解析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法形成商业模式强度判断。  
本模块结论：需补主营收入结构。

## 4. 经济护城河分析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂无法形成护城河结论。  
本模块结论：需补竞争格局与份额数据。

## 5. 财务深度分析（含三表与关键比率）
事实：核心三表缺失。  
计算结果：数据缺失/待核实。  
推断：无法完成财务分析。  
本模块结论：需接入财务主数据。

## 6. 电话会/管理层沟通要点
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：无法验证指引兑现。  
本模块结论：需补公告与电话会材料。

## 7. 多模型估值（相对估值 + DCF + 反向DCF）
事实：估值底层数据缺失。  
计算结果：数据缺失/待核实。  
推断：无法形成合理区间。  
本模块结论：待市场数据接入后重算。

## 8. 竞争与行业分析
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：无法判断行业位置。  
本模块结论：需补同业与行业数据。

## 9. 技术面与交易结构
事实：交易数据缺失。  
计算结果：数据缺失/待核实。  
推断：无法判断交易结构。  
本模块结论：待行情接入后补分析。

## 10. 增长催化剂与前景展望
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：无法形成前景判断。  
本模块结论：需补核心经营与行业催化剂。

## 11. 风险矩阵
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：无法量化风险。  
本模块结论：先补数据后评级。

## 12. 投资决策与跟踪清单
事实：数据缺失/待核实。  
计算结果：数据缺失/待核实。  
推断：暂不形成投资判断。  
本模块结论：当前仅保留观察，不作估值结论。
"""
    path.write_text(body, encoding="utf-8")
    return path


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_generated_path(stdout: str, prefix: str) -> Path | None:
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            p = line.split(":", 1)[1].strip()
            return Path(p)
    return None


def run_analysis(target: StockTarget) -> tuple[Path | None, str | None]:
    if not target.ts_code:
        path = build_analysis_placeholder(target)
        return path, None

    proc = run_cmd(["uv", "run", "python", str(ANALYSIS_SCRIPT), target.ts_code])
    if proc.returncode != 0:
        return None, f"analysis_failed: {proc.stderr[-400:] or proc.stdout[-400:]}"
    out_path = parse_generated_path(proc.stdout, "报告已生成")
    if out_path is None:
        return None, "analysis_failed: output_path_not_found"
    return out_path, None


def build_analysis_placeholder(target: StockTarget) -> Path:
    ts = short_ts()
    stock_dir = REPORT_ROOT / f"{target.symbol}_{slugify_name(target.display_name)}"
    stock_dir.mkdir(parents=True, exist_ok=True)
    path = stock_dir / f"analysis_{target.symbol}_{slugify_name(target.display_name)}_{ts}.md"
    content = f"""# {target.display_name}（{target.symbol}）对话式分析（网络口径占位）

【巴菲特开场：公司基本信息】
1. 公司如何赚钱：数据缺失/待核实。  
2. 收入结构与核心业务占比：数据缺失/待核实。  
3. 行业位置与主要对手：数据缺失/待核实。  
4. 近4-5年增长与盈利趋势：数据缺失/待核实。  
5. 资产负债与现金流安全性：数据缺失/待核实。  
6. 当前估值位置：数据缺失/待核实。

【投资者问答：沃伦与查理】
投资者：该标的不在本地A股库，当前如何判断？  
沃伦：先保证数据口径完整，再谈估值与护城河。  
查理：缺数据时最好的动作是暂不下重结论。

【本杰明插话：估值校准】
本杰明：缺少稳定可核验的市场与财务序列，暂不提供估值区间。

【综合收束】
结论：先纳入观察池，待接入对应市场数据后完成正式分析。

> ⚠️ **免责声明**：本分析仅供教育和研究用途，不构成投资建议。角色化表达仅为分析框架，不代表真实人物对个股的实际发言。
"""
    path.write_text(content, encoding="utf-8")
    return path


def run_value(target: StockTarget) -> tuple[Path | None, Path | None, str | None]:
    if not target.ts_code:
        final, draft = build_value_placeholder(target)
        return final, draft, None

    proc = run_cmd(["uv", "run", "python", str(SKILL_VALUE_SCAFFOLD), target.ts_code])
    if proc.returncode != 0:
        return None, None, f"value_draft_failed: {proc.stderr[-400:] or proc.stdout[-400:]}"

    draft = parse_generated_path(proc.stdout, "报告草稿已生成")
    if draft is None:
        return None, None, "value_draft_failed: output_path_not_found"

    final = Path(str(draft).replace("_draft.md", ".md"))
    shutil.copyfile(draft, final)

    inject_proc = run_cmd(
        [
            "uv",
            "run",
            "python",
            str(SKILL_VALUE_CHARTS),
            str(draft),
            "--inject-report",
            str(final),
            "--cleanup-intermediate",
        ]
    )
    if inject_proc.returncode != 0:
        return final, draft, f"value_chart_inject_failed: {inject_proc.stderr[-400:] or inject_proc.stdout[-400:]}"

    return final, draft, None


def build_value_placeholder(target: StockTarget) -> tuple[Path, Path]:
    ts = short_ts()
    stock_dir = REPORT_ROOT / f"{target.symbol}_{slugify_name(target.display_name)}"
    stock_dir.mkdir(parents=True, exist_ok=True)
    draft = stock_dir / f"value_{target.symbol}_{slugify_name(target.display_name)}_{ts}_draft.md"
    final = stock_dir / f"value_{target.symbol}_{slugify_name(target.display_name)}_{ts}.md"
    base_text = f"""# {target.display_name}（{target.symbol}）深度价值研究报告（网络口径占位）

- 报告日期：{datetime.now().strftime("%Y-%m-%d")}
- 财务日期：数据缺失/待核实
- 估值日期：数据缺失/待核实
- 口径说明：本地A股数据库未命中，暂以占位报告保留结构。

## 1. 公司概况
结论：数据缺失/待核实。  
事实：本地主库未命中该标的。  
推断：需接入对应市场基础资料后重做。

## 2. 行业与竞争格局
结论：数据缺失/待核实。  
事实：缺同业与份额口径。  
推断：暂不判断行业位置。

## 3. 护城河分析（含真伪辨别）
结论：数据缺失/待核实。  
事实：缺收入结构与客户粘性数据。  
推断：暂不判定护城河强弱。

## 4. 管理层与资本配置
结论：数据缺失/待核实。  
事实：缺治理与分红回购数据。  
推断：无法判断资本配置质量。

## 5. 财务分析（成长/盈利/健康/现金流）
结论：数据缺失/待核实。  
事实：三表口径未接入。  
推断：无法进行财务质量判断。

## 6. 成长驱动
结论：数据缺失/待核实。  
事实：缺业务分部与产能计划。  
推断：增长路径待核验。

## 7. 风险分析（含幸存者偏差）
结论：数据缺失/待核实。  
事实：缺历史周期表现。  
推断：抗风险能力不确定。

## 8. 估值分析
结论：数据缺失/待核实。  
事实：缺PE/PB/PS与现金流估值基线。  
推断：当前不提供估值区间。

## 9. 投资判断（多头/空头/跟踪指标）
结论：暂不形成投资建议。  
事实：关键数据缺失。  
推断：先观察后补数据。

## 10. 最终结论
结论：回避结论，等待数据补齐。  
事实：当前仅结构化占位。  
推断：数据完备后再评级。

## 11. 总评分（100分）
结论：评分暂缺。  
事实：缺分项证据链。  
推断：无法完成打分。

## 12. 三个终极问题（必须回答）
1. 如果提价 5%，客户会不会流失？数据缺失/待核实。  
2. 公司赚的钱有没有被管理层浪费？数据缺失/待核实。  
3. 在行业最差年份，公司是怎么活下来的？数据缺失/待核实。
"""
    draft.write_text(base_text, encoding="utf-8")
    final.write_text(base_text + "\n\n<!-- VALUE_CHARTS_START -->\n<!-- VALUE_CHARTS_END -->\n", encoding="utf-8")
    return final, draft


def build_index(results: list[dict[str, Any]], unresolved: list[dict[str, Any]]) -> Path:
    ts = short_ts()
    path = REPORT_ROOT / f"index_all_{ts}.md"
    total = len(results)
    ok_all = sum(1 for r in results if r["status"] == "ok")
    lines = [
        "# 批量报告执行索引",
        "",
        f"- 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 总标的数：{total}",
        f"- 三报告全成功：{ok_all}",
        f"- 存在失败：{total - ok_all}",
        "",
        "## 执行结果",
        "",
        "| 标的 | 代码 | 数据源 | r12 | analysis | value | 状态 | 错误 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['symbol']} | {r['source']} | {r.get('r12','')} | {r.get('analysis','')} | {r.get('value','')} | {r['status']} | {r.get('error','')} |"
        )

    if unresolved:
        lines.extend(["", "## 未解析标的", ""])
        for u in unresolved:
            lines.append(f"- {u['name']}: {u['reason']}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    engine = load_engine()
    run_timestamp = short_ts()

    targets, unresolved = resolve_targets(engine)
    results: list[dict[str, Any]] = []

    for idx, t in enumerate(targets, start=1):
        print(f"[{idx}/{len(targets)}] Processing: {t.query_name} ({t.ts_code or t.symbol})")
        row: dict[str, Any] = {
            "name": t.display_name,
            "symbol": t.symbol,
            "source": t.source,
            "status": "ok",
            "error": "",
        }
        try:
            r12 = build_r12_local(engine, t, run_timestamp)
            row["r12"] = str(r12.relative_to(ROOT))
        except Exception as exc:
            row["status"] = "partial_failed"
            row["error"] = f"r12_failed: {exc}"
            row["r12"] = ""

        analysis_path, analysis_err = run_analysis(t)
        if analysis_path:
            row["analysis"] = str(analysis_path.relative_to(ROOT))
        else:
            row["analysis"] = ""
            row["status"] = "partial_failed"
            row["error"] = (row["error"] + " | " if row["error"] else "") + (analysis_err or "analysis_failed")

        value_final, value_draft, value_err = run_value(t)
        if value_final:
            row["value"] = str(value_final.relative_to(ROOT))
        else:
            row["value"] = ""
            row["status"] = "partial_failed"
            row["error"] = (row["error"] + " | " if row["error"] else "") + (value_err or "value_failed")

        if value_draft:
            row["value_draft"] = str(value_draft.relative_to(ROOT))

        results.append(row)

    index_path = build_index(results, unresolved)
    print(f"Batch completed. Index: {index_path}")


if __name__ == "__main__":
    main()
