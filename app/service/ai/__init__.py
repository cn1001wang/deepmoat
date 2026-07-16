"""AI 分析服务包。

由原 app/service/ai_service.py 拆分而来，职责分离：
- client：通用 chat/completions 客户端（httpx + 响应解析 + 日志）
- context：财务数据上下文构建
- prompts：投资体系 v2 提炼的 prompt 模板
- modes：评分模式枚举（第九章 4 模式 + 自判）
- analyzer：单股票估值分析（第十四章 14.1 / 14.2）
- report：报告落盘

未来扩展：换仓决策（14.3）/ 复盘对话（14.4）复用 client，新增对应模块即可。
"""
import logging
import sys

from app.service.ai.analyzer import generate_valuation
from app.service.ai.modes import AnalysisMode
from app.service.ai.report import save_valuation_report

__all__ = ["generate_valuation", "save_valuation_report", "AnalysisMode"]


# 配置 app.ai logger：子模块（app.ai.xxx）默认 propagate 到此，不再冒泡到 root，
# 避免与 uvicorn/root handler 重复输出。
_ai_logger = logging.getLogger("app.ai")
if not _ai_logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    _ai_logger.addHandler(_h)
    _ai_logger.setLevel(logging.INFO)
    _ai_logger.propagate = False
