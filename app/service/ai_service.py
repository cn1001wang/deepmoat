import httpx
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import StockBasic, Income, BalanceSheet, CashFlow, FinaIndicator
from app.crud.crud_stock import get_stock_by_code


def _build_financial_context(ts_code: str, db: Session, years: int = 5) -> str:
    stock = get_stock_by_code(db, ts_code)
    if not stock:
        return f"未找到股票 {ts_code} 的基本信息。"

    income_list = db.query(Income).filter(Income.ts_code == ts_code).order_by(Income.end_date).all()
    balance_list = db.query(BalanceSheet).filter(BalanceSheet.ts_code == ts_code).order_by(BalanceSheet.end_date).all()
    cashflow_list = db.query(CashFlow).filter(CashFlow.ts_code == ts_code).order_by(CashFlow.end_date).all()
    indicator_list = db.query(FinaIndicator).filter(FinaIndicator.ts_code == ts_code).order_by(FinaIndicator.end_date).all()

    annual_income = [r for r in income_list if r.end_date and r.end_date.endswith("1231")][-years:]
    annual_balance = [r for r in balance_list if r.end_date and r.end_date.endswith("1231")][-years:]
    annual_cashflow = [r for r in cashflow_list if r.end_date and r.end_date.endswith("1231")][-years:]
    annual_indicator = [r for r in indicator_list if r.end_date and r.end_date.endswith("1231")][-years:]

    context_parts = [
        f"# {stock.name} ({ts_code}) 财务数据摘要（近{years}年年报）\n",
    ]

    if annual_indicator:
        context_parts.append("## 核心指标")
        for ind in annual_indicator:
            context_parts.append(
                f"- {ind.end_date}: ROE={ind.roe}, ROIC={ind.roic}, "
                f"毛利率={ind.grossprofit_margin}, 净利率={ind.netprofit_margin}, "
                f"资产负债率={ind.debt_to_assets}, FCF={ind.fcff}, "
                f"营收同比={ind.or_yoy}%, 净利同比={ind.netprofit_yoy}%"
            )

    if annual_income:
        context_parts.append("\n## 利润表")
        for inc in annual_income:
            context_parts.append(
                f"- {inc.end_date}: 营收={inc.revenue}, 净利润={inc.n_income_attr_p}, "
                f"营业利润={inc.operate_profit}, 销售费用={inc.sell_exp}, "
                f"管理费用={inc.admin_exp}, 研发费用={inc.rd_exp}"
            )

    if annual_balance:
        context_parts.append("\n## 资产负债表")
        for bs in annual_balance:
            context_parts.append(
                f"- {bs.end_date}: 总资产={bs.total_assets}, 总负债={bs.total_liab}, "
                f"货币资金={bs.money_cap}, 应收账款={bs.accounts_receiv}, "
                f"存货={bs.inventories}, 商誉={bs.goodwill}, "
                f"净资产={bs.total_hldr_eqy_exc_min_int}"
            )

    if annual_cashflow:
        context_parts.append("\n## 现金流量表")
        for cf in annual_cashflow:
            context_parts.append(
                f"- {cf.end_date}: 经营现金流={cf.n_cashflow_act}, "
                f"投资现金流={cf.n_cashflow_inv_act}, "
                f"筹资现金流={cf.n_cash_flows_fnc_act}, "
                f"自由现金流={cf.free_cashflow}"
            )

    return "\n".join(context_parts)


async def generate_valuation(ts_code: str, db: Session) -> dict:
    if not settings.AI_API_URL or not settings.AI_API_KEY:
        return {
            "analysis": "AI 服务未配置。请在 .env 中设置 AI_API_URL 和 AI_API_KEY。",
            "model_used": "none",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    financial_context = _build_financial_context(ts_code, db)

    system_prompt = """你是一位价值投资分析师，擅长巴菲特/芒格风格的公司分析。
请基于提供的财务数据，输出结构化的估值分析报告，包含：
1. 公司概况（一句话描述商业模式）
2. 财务质量评估（ROE、利润率、现金流质量）
3. 资产负债表安全性
4. 估值分析（根据行业特点选择合适的估值方法）
5. 投资结论（A/B/C/D分类 + 理由）
6. 主要风险（至少3条）
7. 跟踪指标

输出格式为 Markdown。所有判断必须引用具体数据。"""

    user_prompt = f"""请分析以下公司的投资价值：

{financial_context}

请给出完整的估值分析。"""

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            settings.AI_API_URL,
            headers={
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.AI_MODEL,
                "max_tokens": 4096,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data.get("content", [{}])
    if isinstance(content, list) and len(content) > 0:
        analysis_text = content[0].get("text", "")
    else:
        analysis_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    return {
        "analysis": analysis_text,
        "model_used": settings.AI_MODEL,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def save_valuation_report(ts_code: str, content: str, db: Session) -> str:
    stock = get_stock_by_code(db, ts_code)
    name = stock.name if stock else "unknown"
    symbol = ts_code.split(".")[0]
    timestamp = datetime.now().strftime("%y%m%d%H%M")

    dir_path = Path("outputs/reports") / f"{symbol}_{name}"
    dir_path.mkdir(parents=True, exist_ok=True)

    filename = f"ai_valuation_{symbol}_{name}_{timestamp}.md"
    file_path = dir_path / filename
    file_path.write_text(content, encoding="utf-8")

    return str(file_path)
