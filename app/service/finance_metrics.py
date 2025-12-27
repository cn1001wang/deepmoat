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
    "revenue", "n_income", "n_income_attr_p",
    "operate_profit", "basic_eps",
]

BALANCE_COLUMNS = [
    "total_assets", "total_liab",
]

CASHFLOW_COLUMNS = [
    "n_cashflow_act",
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

    merged = merge_frames([income, balance, cash])
    if merged.empty:
        return {"periods": [], "rows": []}

    periods = list(merged["end_date"])

    assets_map = dict(zip(merged["end_date"], merged["total_assets"]))
    assets_yoy = yoy(assets_map, "1231")

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
    ]

    return {"periods": periods, "rows": rows}
