"""
财务指标计算服务
"""
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

from app.service.tushare_service import (
    get_income_all,
    get_balancesheet_all,
    get_cashflow_all,
    fetch_fina_indicator,
)
from app.utils.date_utils import generate_periods
from app.utils.df_utils import dedup_finance_df
from app.utils.finance_df import (
    ensure_columns,
    filter_periods,
    merge_frames,
    safe_div,
    yoy,
    to_billion,
    format_percent,
)

INCOME_COLUMNS = [
    "revenue",
    "n_income",
    "n_income_attr_p",
    "operate_profit",
    "basic_eps",
]

BALANCE_COLUMNS = [
    "total_assets",
    "total_liab",
    "money_cap",
]

CASHFLOW_COLUMNS = [
    "n_cashflow_act",
    "n_incr_cash_cash_equ",
]

# 需要的财务指标字段（tushare fina_indicator）
INDICATOR_COLUMNS = [
    # 比率类
    "grossprofit_margin",  # 销售毛利率
    "netprofit_margin",    # 销售净利率
    "op_of_gr",            # 营业利润/营业总收入
    "expense_of_sales",    # 销售期间费用率
    "roe",                 # 净资产收益率
    # 规模类
    "fixed_assets",        # 固定资产合计
    "interestdebt",        # 带息债务
]


def build_metrics_table(ts_code: str, years: int = 6) -> Dict[str, Any]:
    """
    构建前端财务指标表
    """
    income = filter_periods(
        ensure_columns(get_income_all(ts_code), INCOME_COLUMNS),
        years
    )
    balance = filter_periods(
        ensure_columns(get_balancesheet_all(ts_code), BALANCE_COLUMNS),
        years
    )
    cash = filter_periods(
        ensure_columns(get_cashflow_all(ts_code), CASHFLOW_COLUMNS),
        years
    )
    indicator = filter_periods(
        ensure_columns(fetch_fina_indicator(ts_code), INDICATOR_COLUMNS),
        years
    )

    merged = merge_frames([income, balance, cash, indicator])
    if merged.empty:
        return {"periods": [], "rows": []}

    periods = list(merged["end_date"])

    assets_map = dict(zip(merged["end_date"], merged["total_assets"]))
    assets_yoy = yoy(assets_map, "1231")

    def col_list(name: str):
        return list(merged[name]) if name in merged.columns else []

    rows = [
        {
            "label": "资产合计",
            "key": "total_assets",
            "unit": "亿",
            "category": "资产扩张能力",
            "values": [to_billion(v) for v in merged["total_assets"]],
        },
        {
            "label": "资产合计同比",
            "key": "assets_yoy",
            "unit": "%",
            "category": "资产扩张能力",
            "values": [format_percent(assets_yoy.get(p)) for p in periods],
        },
        {
            "label": "资产负债率",
            "key": "debt_ratio",
            "unit": "%",
            "category": "业务风险",
            "values": [
                format_percent(safe_div(l, a))
                for l, a in zip(
                    merged["total_liab"],
                    merged["total_assets"]
                )
            ],
        },
        {
            "label": "负债合计",
            "key": "total_liab",
            "unit": "亿",
            "category": "业务风险",
            "values": [to_billion(v) for v in col_list("total_liab")],
        },
        {
            "label": "带息债务总额",
            "key": "interestdebt",
            "unit": "亿",
            "category": "业务风险",
            "values": [to_billion(v) for v in col_list("interestdebt")],
        },
        {
            "label": "货币资金",
            "key": "money_cap",
            "unit": "亿",
            "category": "业务风险",
            "values": [to_billion(v) for v in col_list("money_cap")],
        },
        {
            "label": "营业收入",
            "key": "revenue",
            "unit": "亿",
            "category": "成长能力",
            "values": [to_billion(v) for v in col_list("revenue")],
        },
        {
            "label": "营业收入同比",
            "key": "revenue_yoy",
            "unit": "%",
            "category": "成长能力",
            "values": [
                format_percent(
                    yoy(
                        dict(zip(merged["end_date"], col_list("revenue"))),
                        "1231"
                    ).get(p)
                )
                for p in periods
            ],
        },
        {
            "label": "毛利率",
            "key": "gross_margin",
            "unit": "%",
            "category": "竞争力",
            "values": col_list("grossprofit_margin"),
        },
        {
            "label": "销售期间费用率",
            "key": "expense_rate",
            "unit": "%",
            "category": "成本控制能力",
            "values": col_list("expense_of_sales"),
        },
        {
            "label": "营业利润率",
            "key": "operating_profit_margin",
            "unit": "%",
            "category": "主营盈利能力",
            "values": col_list("op_of_gr"),
        },
        {
            "label": "净利率",
            "key": "net_margin",
            "unit": "%",
            "category": "综合盈利能力",
            "values": col_list("netprofit_margin"),
        },
        {
            "label": "ROE",
            "key": "roe",
            "unit": "%",
            "category": "综合盈利能力",
            "values": col_list("roe"),
        },
        {
            "label": "经营性现金流",
            "key": "operating_cash_flow",
            "unit": "亿",
            "category": "造血能力",
            "values": [to_billion(v) for v in col_list("n_cashflow_act")],
        },
        {
            "label": "现金净增加额",
            "key": "net_increase_in_cash",
            "unit": "亿",
            "category": "稳定性",
            "values": [to_billion(v) for v in col_list("n_incr_cash_cash_equ")],
        },
        {
            "label": "固定资产合计",
            "key": "fixed_assets",
            "unit": "亿",
            "category": "固定资产",
            "values": [to_billion(v) for v in col_list("fixed_assets")],
        },
    ]

    return {"periods": periods, "rows": rows}
