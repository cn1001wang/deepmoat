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
from app.db.session import SessionLocal
from app.crud.crud_dividend import get_dividend_by_ts_code
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
    # Added
    "oper_cost",
    "biz_tax_surchg",
    "sell_exp",
    "admin_exp",
    "fin_exp",
    "total_profit",
    "non_oper_income",
    "div_payt",  # Dividend payout
]

BALANCE_COLUMNS = [
    "total_assets",
    "total_liab",
    "money_cap",
    # Added
    "accounts_receiv",
    "notes_receiv",
    "prepayment",
    "acct_payable",
    "notes_payable",
    "adv_receipts",
    "fix_assets",
    "cip",
    "invest_real_estate",
    "lt_eqt_invest",
    "fa_avail_for_sale",
    "oth_eq_invest",
    "oth_illiq_fin_assets",
    "deriv_assets",
    "trad_asset",
]

CASHFLOW_COLUMNS = [
    "n_cashflow_act",
    "n_incr_cash_cash_equ",
    # Added
    "n_cashflow_inv_act",
    "n_cash_flows_fnc_act",
    "c_pay_acq_const_fiolta",
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
    # Added
    "profit_dedt",         # 扣除非经常性损益后的净利润
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

    # Helpers
    def col_list(name: str):
        return list(merged[name].fillna(0)) if name in merged.columns else [0.0] * len(periods)

    def get_yoy(name: str):
        val_map = dict(zip(merged["end_date"], col_list(name)))
        yoy_map = yoy(val_map)
        return [format_percent(yoy_map.get(p)) for p in periods]

    # Pre-calculate derived data for convenience
    money_cap = col_list("money_cap")
    interestdebt = col_list("interestdebt")
    total_assets = col_list("total_assets")
    total_liab = col_list("total_liab")
    revenue = col_list("revenue")
    
    # Industry Status
    ap_total = [
        a + b + c 
        for a, b, c in zip(col_list("acct_payable"), col_list("notes_payable"), col_list("adv_receipts"))
    ]
    ar_total = [
        a + b + c
        for a, b, c in zip(col_list("accounts_receiv"), col_list("notes_receiv"), col_list("prepayment"))
    ]
    
    # Fixed Assets
    fix_total = [a + b for a, b in zip(col_list("fix_assets"), col_list("cip"))]
    
    # Focus
    invest_total = [
        a + b + c + d + e + f + g
        for a, b, c, d, e, f, g in zip(
            # 交易性金融资产
            col_list("trad_asset"),
            # 衍生金融资产
            col_list("deriv_assets"),
            # 长期股权投资
            col_list("lt_eqt_invest"),
            # 可供出售金融资产
            col_list("fa_avail_for_sale"),
            #其他权益工具投资
            col_list("oth_eq_invest"),
            #其他非流动金融资产
            col_list("oth_illiq_fin_assets"),
            # 投资性房地产
            col_list("invest_real_estate"),
        )
    ]

    # Core Profit
    # revenue - cost - taxes - sell_exp - admin_exp - fin_exp
    main_profit = [
        rev - cost - tax - sell - admin - fin
        for rev, cost, tax, sell, admin, fin in zip(
            revenue,
            col_list("oper_cost"),
            col_list("biz_tax_surchg"),
            col_list("sell_exp"),
            col_list("admin_exp"),
            col_list("fin_exp")
        )
    ]

    rows = []

    # 1. 资产扩展能力
    rows.append({
        "label": "资产合计",
        "key": "total_assets",
        "unit": "亿",
        "category": "资产扩张能力",
        "values": [to_billion(v) for v in total_assets],
    })
    rows.append({
        "label": "资产合计同比",
        "key": "assets_yoy",
        "unit": "%",
        "category": "资产扩张能力",
        "values": get_yoy("total_assets"),
    })

    # 2. 债务风险
    rows.append({
        "label": "资产负债率",
        "key": "debt_ratio",
        "unit": "%",
        "category": "债务风险",
        "values": [format_percent(safe_div(l, a)) for l, a in zip(total_liab, total_assets)],
    })
    rows.append({
        "label": "有息负债总额",
        "key": "interestdebt",
        "unit": "亿",
        "category": "债务风险",
        "values": [to_billion(v) for v in interestdebt],
    })
    rows.append({
        "label": "货币资金",
        "key": "money_cap",
        "unit": "亿",
        "category": "债务风险",
        "values": [to_billion(v) for v in money_cap],
    })
    rows.append({
        "label": "货币资金 - 有息负债",
        "key": "money_minus_debt",
        "unit": "亿",
        "category": "债务风险",
        "values": [to_billion(m - d) for m, d in zip(money_cap, interestdebt)],
    })
    rows.append({
        "label": "货币资金 / 资产合计",
        "key": "money_to_assets",
        "unit": "%",
        "category": "债务风险",
        "values": [format_percent(safe_div(m, a)) for m, a in zip(money_cap, total_assets)],
    })

    # 3. 行业地位
    rows.append({
        "label": "应付(+预收) - 应收(+预付)",
        "key": "ap_minus_ar",
        "unit": "亿",
        "category": "行业地位",
        "values": [to_billion(ap - ar) for ap, ar in zip(ap_total, ar_total)],
    })

    # 4. 收入结构
    rows.append({
        "label": "应收账款 / 资产总计",
        "key": "ar_to_assets",
        "unit": "%",
        "category": "收入结构",
        "values": [format_percent(safe_div(v, a)) for v, a in zip(col_list("accounts_receiv"), total_assets)],
    })
    rows.append({
        "label": "应收账款 / 营业收入",
        "key": "ar_to_revenue",
        "unit": "%",
        "category": "收入结构",
        "values": [format_percent(safe_div(v, r)) for v, r in zip(col_list("accounts_receiv"), revenue)],
    })
    rows.append({
        "label": "预付款项 / 营业收入",
        "key": "prepayment_to_revenue",
        "unit": "%",
        "category": "收入结构",
        "values": [format_percent(safe_div(v, r)) for v, r in zip(col_list("prepayment"), revenue)],
    })

    # 5. 固定资产
    rows.append({
        "label": "固定资产+在建工程",
        "key": "fix_total",
        "unit": "亿",
        "category": "固定资产",
        "values": [to_billion(v) for v in fix_total],
    })
    rows.append({
        "label": "三者之和 / 总资产",
        "key": "fix_to_assets",
        "unit": "%",
        "category": "固定资产",
        "values": [format_percent(safe_div(v, a)) for v, a in zip(fix_total, total_assets)],
    })

    # 6. 专注度
    rows.append({
        "label": "投资类资产 / 总资产",
        "key": "invest_to_assets",
        "unit": "%",
        "category": "专注度",
        "values": [format_percent(safe_div(v, a)) for v, a in zip(invest_total, total_assets)],
        # "values": invest_total,
    })

    # 7. 成长能力
    rows.append({
        "label": "营业收入",
        "key": "revenue",
        "unit": "亿",
        "category": "成长能力",
        "values": [to_billion(v) for v in revenue],
    })
    rows.append({
        "label": "营业收入同比",
        "key": "revenue_yoy",
        "unit": "%",
        "category": "成长能力",
        "values": get_yoy("revenue"),
    })

    # 8. 竞争力
    rows.append({
        "label": "毛利率",
        "key": "gross_margin",
        "unit": "%",
        "category": "竞争力",
        "values": col_list("grossprofit_margin"),
    })
    rows.append({
        "label": "净利率",
        "key": "net_margin",
        "unit": "%",
        "category": "竞争力",
        "values": col_list("netprofit_margin"),
    })
    
    # 9. 成本控制能力
    rows.append({
        "label": "费用率",
        "key": "expense_rate",
        "unit": "%",
        "category": "成本控制能力",
        "values": col_list("expense_of_sales"),
    })
    # expense_rate / gross_margin
    # Assuming both are percentages (e.g. 20, 50). 20/50 = 0.4 -> 40%.
    rows.append({
        "label": "费用率 / 毛利率",
        "key": "expense_to_gross",
        "unit": "%",
        "category": "成本控制能力",
        "values": [
            format_percent(safe_div(e, g)) 
            for e, g in zip(col_list("expense_of_sales"), col_list("grossprofit_margin"))
        ],
    })

    # 10. 主业盈利能力
    rows.append({
        "label": "主营利润率",
        "key": "main_profit_margin",
        "unit": "%",
        "category": "主业盈利能力",
        "values": [format_percent(safe_div(m, r)) for m, r in zip(main_profit, revenue)],
    })
    rows.append({
        "label": "主营利润 / 利润总额",
        "key": "main_to_total_profit",
        "unit": "%",
        "category": "主业盈利能力",
        "values": [format_percent(safe_div(m, t)) for m, t in zip(main_profit, col_list("total_profit"))],
    })
    rows.append({
        "label": "营业外收入 / 利润总额",
        "key": "non_op_to_total_profit",
        "unit": "%",
        "category": "主业盈利能力",
        "values": [format_percent(safe_div(n, t)) for n, t in zip(col_list("non_oper_income"), col_list("total_profit"))],
    })
    rows.append({
        "label": "营业利润率",
        "key": "op_margin",
        "unit": "%",
        "category": "主业盈利能力",
        "values": col_list("op_of_gr"),
    })

    # 11. 经营成果及含金量
    rows.append({
        "label": "净利润",
        "key": "n_income",
        "unit": "亿",
        "category": "经营成果及含金量",
        "values": [to_billion(v) for v in col_list("n_income")],
    })
    rows.append({
        "label": "净利润同比",
        "key": "n_income_yoy",
        "unit": "%",
        "category": "经营成果及含金量",
        "values": get_yoy("n_income"),
    })
    rows.append({
        "label": "净利润现金比率",
        "key": "ocf_to_net_profit",
        "unit": "%",
        "category": "经营成果及含金量",
        "values": [format_percent(safe_div(o, n)) for o, n in zip(col_list("n_cashflow_act"), col_list("n_income"))],
    })
    rows.append({
        "label": "扣非后归母净利润",
        "key": "profit_dedt",
        "unit": "亿",
        "category": "经营成果及含金量",
        "values": [to_billion(v) for v in col_list("profit_dedt")],
    })
    rows.append({
        "label": "归母净利润",
        "key": "n_income_attr_p",
        "unit": "亿",
        "category": "经营成果及含金量",
        "values": [to_billion(v) for v in col_list("n_income_attr_p")],
    })
    rows.append({
        "label": "归母净利润同比",
        "key": "n_income_attr_p_yoy",
        "unit": "%",
        "category": "经营成果及含金量",
        "values": get_yoy("n_income_attr_p"),
    })

    # 12. 综合盈利能力
    rows.append({
        "label": "ROE",
        "key": "roe",
        "unit": "%",
        "category": "综合盈利能力",
        "values": col_list("roe"),
    })
    rows.append({
        "label": "基本每股收益",
        "key": "basic_eps",
        "unit": "元",
        "category": "综合盈利能力",
        "values": col_list("basic_eps"),
    })

    # 13. 造血能力
    rows.append({
        "label": "经营活动产生的现金流量净额",
        "key": "ocf",
        "unit": "亿",
        "category": "造血能力",
        "values": [to_billion(v) for v in col_list("n_cashflow_act")],
    })

    # 14. 未来成长
    capex = col_list("c_pay_acq_const_fiolta")
    rows.append({
        "label": "购建/经营活动现金流净额",
        "key": "capex_to_ocf",
        "unit": "%",
        "category": "未来成长",
        "values": [format_percent(safe_div(c, o)) for c, o in zip(capex, col_list("n_cashflow_act"))],
    })

    # 15. 公司品质
    with SessionLocal() as db:
        dividends = get_dividend_by_ts_code(db, ts_code)
        best_records = {} # end_date -> record
        for div in dividends:
            # 仅保留已实施的分红记录
            if str(div.div_proc) != "实施":
                continue

            curr = best_records.get(div.end_date)
            if not curr:
                best_records[div.end_date] = div
            else:
                # 如果同一 end_date 有多条实施记录（罕见，可能是修正），取 ann_date 最新的
                if div.ann_date > curr.ann_date:
                    best_records[div.end_date] = div

        # Step 2: Sum by year
        year_dividends = {} # year (int) -> total cash (float)
        for end_date, div in best_records.items():
            if not end_date or len(end_date) < 4:
                continue
            year = int(end_date[:4])
            # cash_div_tax is per share (yuan). base_share is in 10k shares.
            # Total = cash_div_tax * (base_share * 10000)
            if div.cash_div_tax and div.base_share:
                total = div.cash_div_tax * div.base_share * 10000
                year_dividends[year] = year_dividends.get(year, 0.0) + total

    div_payout_values = []
    for p, n_income in zip(periods, col_list("n_income_attr_p")):
        # p is like '20221231'
        if not p or len(p) < 4:
            div_payout_values.append(None)
            continue
        year = int(p[:4])
        total_div = year_dividends.get(year, 0.0)

        # Payout Ratio = Total Dividend / Net Income
        val = format_percent(safe_div(total_div, n_income))
        div_payout_values.append(val)

    rows.append({
        "label": "股利支付率",
        "key": "dividend_payout",
        "unit": "%",
        "category": "公司品质",
        "values": div_payout_values,
    })

    # 16. 发展阶段
    def get_cash_type(act, inv, fin):
        def sign(x): return "+" if x > 0 else "-"
        return f"{sign(act)}{sign(inv)}{sign(fin)}"

    rows.append({
        "label": "三大现金流类型",
        "key": "cash_types",
        "unit": "",
        "category": "发展阶段",
        "values": [
            get_cash_type(a, i, f)
            for a, i, f in zip(
                col_list("n_cashflow_act"),
                col_list("n_cashflow_inv_act"),
                col_list("n_cash_flows_fnc_act")
            )
        ],
    })

    # 17. 稳定性
    rows.append({
        "label": "现金及现金等价物净增加额",
        "key": "net_increase_cash",
        "unit": "亿",
        "category": "稳定性",
        "values": [to_billion(v) for v in col_list("n_incr_cash_cash_equ")],
    })

    return {"periods": periods, "rows": rows}
