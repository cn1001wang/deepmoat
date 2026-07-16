"""构建喂给 AI 的财务数据上下文（投资体系 v2 第五/七章所需）。

在原四大报表摘要基础上，补充公司画像（行业 / 主营业务 / 审计意见），
用于支撑第十四章 14.1 入选理由与 14.2 产业链定位输出。
"""
import logging

from sqlalchemy.orm import Session

from app.crud.crud_stock import get_stock_by_code
from app.models.models import (
    BalanceSheet,
    CashFlow,
    FinaAudit,
    FinaIndicator,
    Income,
    StockCompany,
)

logger = logging.getLogger("app.ai.context")


def build_financial_context(ts_code: str, db: Session, years: int = 5) -> str:
    stock = get_stock_by_code(db, ts_code)
    if not stock:
        return f"未找到股票 {ts_code} 的基本信息。"

    income_list = db.query(Income).filter(Income.ts_code == ts_code).order_by(Income.end_date).all()
    balance_list = db.query(BalanceSheet).filter(BalanceSheet.ts_code == ts_code).order_by(BalanceSheet.end_date).all()
    cashflow_list = db.query(CashFlow).filter(CashFlow.ts_code == ts_code).order_by(CashFlow.end_date).all()
    indicator_list = db.query(FinaIndicator).filter(FinaIndicator.ts_code == ts_code).order_by(FinaIndicator.end_date).all()

    annual_income = _annual(income_list, years)
    annual_balance = _annual(balance_list, years)
    annual_cashflow = _annual(cashflow_list, years)
    annual_indicator = _annual(indicator_list, years)

    parts: list[str] = [f"# {stock.name} ({ts_code}) 财务数据摘要（近{years}年年报）\n"]

    # 公司画像 + 产业链线索（14.1 入选理由、14.2 产业链定位、第四章排雷所需）
    company = db.query(StockCompany).filter(StockCompany.ts_code == ts_code).first()
    parts.append("## 公司画像")
    parts.append(f"- 行业：{stock.industry or '未知'}")
    if company:
        main_bz = (company.main_business or "").strip()
        if main_bz:
            parts.append(f"- 主营业务：{main_bz[:500]}")
    audit = (
        db.query(FinaAudit)
        .filter(FinaAudit.ts_code == ts_code)
        .order_by(FinaAudit.end_date.desc())
        .first()
    )
    if audit:
        parts.append(f"- 最新审计意见（{audit.end_date}）：{audit.audit_result or '未知'}")

    if annual_indicator:
        parts.append("\n## 核心指标")
        for ind in annual_indicator:
            parts.append(
                f"- {ind.end_date}: ROE={ind.roe}, ROIC={ind.roic}, "
                f"毛利率={ind.grossprofit_margin}, 净利率={ind.netprofit_margin}, "
                f"资产负债率={ind.debt_to_assets}, FCF={ind.fcff}, "
                f"营收同比={ind.or_yoy}%, 净利同比={ind.netprofit_yoy}%"
            )

    if annual_income:
        parts.append("\n## 利润表")
        for inc in annual_income:
            parts.append(
                f"- {inc.end_date}: 营收={inc.revenue}, 净利润={inc.n_income_attr_p}, "
                f"营业利润={inc.operate_profit}, 销售费用={inc.sell_exp}, "
                f"管理费用={inc.admin_exp}, 研发费用={inc.rd_exp}"
            )

    if annual_balance:
        parts.append("\n## 资产负债表")
        for bs in annual_balance:
            parts.append(
                f"- {bs.end_date}: 总资产={bs.total_assets}, 总负债={bs.total_liab}, "
                f"货币资金={bs.money_cap}, 应收账款={bs.accounts_receiv}, "
                f"存货={bs.inventories}, 商誉={bs.goodwill}, "
                f"净资产={bs.total_hldr_eqy_exc_min_int}"
            )

    if annual_cashflow:
        parts.append("\n## 现金流量表")
        for cf in annual_cashflow:
            parts.append(
                f"- {cf.end_date}: 经营现金流={cf.n_cashflow_act}, "
                f"投资现金流={cf.n_cashflow_inv_act}, "
                f"筹资现金流={cf.n_cash_flows_fnc_act}, "
                f"自由现金流={cf.free_cashflow}"
            )

    return "\n".join(parts)


def _annual(rows, years: int):
    """取近 N 年年报（end_date 以 1231 结尾）。"""
    return [r for r in rows if r.end_date and r.end_date.endswith("1231")][-years:]
