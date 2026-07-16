"""单股票 AI 估值分析（高层编排）。

组合 context + prompts + client，对应投资体系 v2 第十四章 14.1 / 14.2。
换仓决策（14.3）/ 复盘对话（14.4）未来可在本包新增模块，复用 client。
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.service.ai.client import AIConfigError, chat
from app.service.ai.context import build_financial_context
from app.service.ai.modes import AnalysisMode
from app.service.ai.prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger("app.ai.analyzer")


async def generate_valuation(
    ts_code: str,
    db: Session,
    mode: AnalysisMode | None = None,
) -> dict:
    """生成单股票估值分析报告。

    mode=None 或 AUTO 时由 AI 按 9.1 决策树自判；否则按指定模式评分维度输出。
    返回 {analysis, model_used, mode_used, generated_at}。
    """
    effective_mode = mode or AnalysisMode.AUTO

    try:
        financial_context = build_financial_context(ts_code, db)
        system_prompt = build_system_prompt(effective_mode)
        user_prompt = build_user_prompt(financial_context, effective_mode)

        logger.info("[AI] valuation ts_code=%s mode=%s", ts_code, effective_mode.value)
        analysis_text = await chat(system_prompt, user_prompt)
    except AIConfigError:
        return {
            "analysis": "AI 服务未配置。请在 .env 中设置 AI_API_URL 和 AI_API_KEY。",
            "model_used": "none",
            "mode_used": effective_mode.value,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    return {
        "analysis": analysis_text,
        "model_used": settings.AI_API_MODEL,
        "mode_used": effective_mode.value,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
