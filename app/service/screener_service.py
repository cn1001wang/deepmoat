from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.models import (
    StockBasic, FinaIndicator, BalanceSheet, CashFlow, Income,
    DailyBasic, FinaAudit, Dividend,
)

STRATEGY_DEFAULTS = {
    "稳健价值型": {
        "min_roe": 10,
        "max_debt_ratio": 60,
        "min_cashflow_ratio": 0.8,
        "max_goodwill_ratio": 20,
        "min_dividend_yield": 2,
    },
    "高质量成长型": {
        "min_roe": 15,
        "max_debt_ratio": 60,
        "min_cashflow_ratio": 0.8,
        "min_revenue_cagr": 8,
        "min_profit_cagr": 8,
    },
    "高股息低估值型": {
        "min_dividend_yield": 3,
        "min_consecutive_dividends": 5,
        "max_pe_percentile": 30,
    },
    "困境反转型": {
        "max_pb_percentile": 20,
        "max_debt_ratio": 70,
    },
}

# PLACEHOLDER_SCREENER_IMPL

def run_screener(db: Session, strategy: str, params: dict, years: int = 5) -> dict:
    defaults = STRATEGY_DEFAULTS.get(strategy, STRATEGY_DEFAULTS["稳健价值型"])
    config = {**defaults, **params}

    all_stocks = db.query(StockBasic).filter(StockBasic.list_status == "L").all()
    total = len(all_stocks)

    results = []
    eliminated = 0

    for stock in all_stocks:
        ts_code = stock.ts_code
        name = stock.name

        if "ST" in (name or ""):
            eliminated += 1
            continue

        indicators = (
            db.query(FinaIndicator)
            .filter(
                FinaIndicator.ts_code == ts_code,
                FinaIndicator.end_date.like("%1231"),
            )
            .order_by(FinaIndicator.end_date.desc())
            .limit(years)
            .all()
        )

        if len(indicators) < 3:
            eliminated += 1
            continue

        roe_values = [i.roe for i in indicators if i.roe is not None]
        if not roe_values:
            eliminated += 1
            continue
        avg_roe = sum(roe_values) / len(roe_values)

        min_roe = config.get("min_roe", 10)
        if avg_roe < min_roe:
            eliminated += 1
            continue

        debt_values = [i.debt_to_assets for i in indicators if i.debt_to_assets is not None]
        if debt_values:
            latest_debt = debt_values[0]
            max_debt = config.get("max_debt_ratio", 60)
            industry = stock.industry or ""
            exempt = any(k in industry for k in ["银行", "保险", "券商", "地产", "电力"])
            if not exempt and latest_debt > max_debt:
                eliminated += 1
                continue

        cashflows = (
            db.query(CashFlow)
            .filter(
                CashFlow.ts_code == ts_code,
                CashFlow.end_date.like("%1231"),
            )
            .order_by(CashFlow.end_date.desc())
            .limit(years)
            .all()
        )

        ocf_values = [c.n_cashflow_act for c in cashflows if c.n_cashflow_act is not None]
        if ocf_values:
            ocf_sum = sum(ocf_values)
            if ocf_sum < 0:
                eliminated += 1
                continue

        incomes = (
            db.query(Income)
            .filter(
                Income.ts_code == ts_code,
                Income.end_date.like("%1231"),
            )
            .order_by(Income.end_date.desc())
            .limit(years)
            .all()
        )

        net_profit_values = [inc.n_income_attr_p for inc in incomes if inc.n_income_attr_p is not None]
        profit_sum = sum(net_profit_values) if net_profit_values else 0

        cashflow_ratio = None
        if profit_sum > 0 and ocf_values:
            cashflow_ratio = sum(ocf_values) / profit_sum

        min_cf_ratio = config.get("min_cashflow_ratio", 0)
        if min_cf_ratio and cashflow_ratio is not None and cashflow_ratio < min_cf_ratio:
            eliminated += 1
            continue

        score = _calculate_score(avg_roe, debt_values, cashflow_ratio, roe_values, ocf_values, net_profit_values, indicators)

        results.append({
            "tsCode": ts_code,
            "name": name,
            "industry": stock.industry,
            "avgRoe": round(avg_roe, 2),
            "debtRatio": round(debt_values[0], 2) if debt_values else None,
            "cashflowRatio": round(cashflow_ratio, 2) if cashflow_ratio else None,
            "score": score,
            "risks": _check_risks_inline(ts_code, name, indicators, cashflows),
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "stocks": results[:50],
        "meta": {
            "total": total,
            "eliminated": eliminated,
            "passed": len(results),
            "strategy": strategy,
            "config": config,
        },
    }


def _calculate_score(avg_roe, debt_values, cashflow_ratio, roe_values, ocf_values, net_profit_values, indicators) -> int:
    score = 0

    if avg_roe >= 20:
        score += 8
    elif avg_roe >= 15:
        score += 6
    elif avg_roe >= 10:
        score += 4
    elif avg_roe >= 5:
        score += 2

    roic_values = [i.roic for i in indicators if i.roic is not None]
    if roic_values:
        avg_roic = sum(roic_values) / len(roic_values)
        if avg_roic and avg_roic >= 15:
            score += 5
        elif avg_roic and avg_roic >= 10:
            score += 4
        elif avg_roic and avg_roic >= 7:
            score += 2

    gm_values = [i.grossprofit_margin for i in indicators if i.grossprofit_margin is not None]
    if gm_values:
        avg_gm = sum(gm_values) / len(gm_values)
        import statistics
        gm_std = statistics.stdev(gm_values) if len(gm_values) > 1 else 0
        if gm_std < 3 and avg_gm > 30:
            score += 5
        elif gm_std < 5:
            score += 3
        else:
            score += 1

    if cashflow_ratio:
        if cashflow_ratio >= 1.2:
            score += 7
        elif cashflow_ratio >= 1.0:
            score += 5
        elif cashflow_ratio >= 0.8:
            score += 3
        elif cashflow_ratio >= 0.6:
            score += 1

    if ocf_values:
        positive_count = sum(1 for v in ocf_values if v > 0)
        if positive_count == len(ocf_values):
            score += 8
        elif positive_count >= len(ocf_values) - 1:
            score += 6
        elif positive_count >= len(ocf_values) - 2:
            score += 4

    if debt_values:
        d = debt_values[0]
        if d < 30:
            score += 5
        elif d < 40:
            score += 4
        elif d < 50:
            score += 3
        elif d < 60:
            score += 2
        elif d < 70:
            score += 1

    if net_profit_values and len(net_profit_values) >= 2:
        first = net_profit_values[-1]
        last = net_profit_values[0]
        if first and last and first > 0 and last > 0:
            n = len(net_profit_values) - 1
            ratio = last / first
            if ratio > 0:
                cagr = (ratio ** (1 / n) - 1) * 100
                if cagr > 15:
                    score += 5
                elif cagr > 10:
                    score += 4
                elif cagr > 5:
                    score += 3
                elif cagr > 0:
                    score += 1

    return min(score, 100)


def _check_risks_inline(ts_code, name, indicators, cashflows) -> list:
    risks = []
    if indicators and indicators[0].debt_to_assets and indicators[0].debt_to_assets > 50:
        risks.append({"type": "leverage", "detail": f"资产负债率 {indicators[0].debt_to_assets:.1f}%", "severity": "medium"})
    return risks


def check_risk(db: Session, ts_code: str) -> dict:
    stock = db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()
    if not stock:
        return {"passed": False, "risks": [{"type": "not_found", "detail": "股票不存在", "severity": "high"}]}

    risks = []
    name = stock.name or ""

    if "ST" in name:
        risks.append({"type": "st", "detail": "ST 或 *ST 标记", "severity": "high"})

    indicators = (
        db.query(FinaIndicator)
        .filter(FinaIndicator.ts_code == ts_code, FinaIndicator.end_date.like("%1231"))
        .order_by(FinaIndicator.end_date.desc())
        .limit(5)
        .all()
    )

    if indicators and indicators[0].debt_to_assets and indicators[0].debt_to_assets > 70:
        risks.append({"type": "leverage", "detail": f"资产负债率 {indicators[0].debt_to_assets:.1f}% > 70%", "severity": "high"})

    cashflows = (
        db.query(CashFlow)
        .filter(CashFlow.ts_code == ts_code, CashFlow.end_date.like("%1231"))
        .order_by(CashFlow.end_date.desc())
        .limit(5)
        .all()
    )
    ocf_values = [c.n_cashflow_act for c in cashflows if c.n_cashflow_act is not None]
    if ocf_values and sum(ocf_values) < 0:
        risks.append({"type": "cashflow", "detail": "近5年经营现金流累计为负", "severity": "high"})

    balances = (
        db.query(BalanceSheet)
        .filter(BalanceSheet.ts_code == ts_code, BalanceSheet.end_date.like("%1231"))
        .order_by(BalanceSheet.end_date.desc())
        .limit(1)
        .all()
    )
    if balances:
        bs = balances[0]
        goodwill = bs.goodwill or 0
        equity = bs.total_hldr_eqy_exc_min_int or 1
        if equity > 0 and goodwill / equity > 0.3:
            risks.append({"type": "goodwill", "detail": f"商誉/净资产 = {goodwill/equity*100:.1f}% > 30%", "severity": "high"})

    audits = (
        db.query(FinaAudit)
        .filter(FinaAudit.ts_code == ts_code)
        .order_by(FinaAudit.ann_date.desc())
        .limit(1)
        .all()
    )
    if audits and audits[0].audit_result and "标准无保留" not in audits[0].audit_result:
        risks.append({"type": "audit", "detail": f"审计意见: {audits[0].audit_result}", "severity": "high"})

    passed = not any(r["severity"] == "high" for r in risks)
    return {"passed": passed, "risks": risks}
