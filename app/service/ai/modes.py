"""分析模式定义（对应投资体系 v2 第九章）。

4 种评分模式 + 1 个自动判断模式。AUTO 时由 AI 按 9.1 决策树自判模式并在
输出中声明；其余模式按对应章节的评分维度约束 AI 输出。
"""
from enum import Enum


class AnalysisMode(str, Enum):
    """单股票分析评分模式。"""

    AUTO = "auto"        # 由 AI 按 9.1 决策树自判
    STEADY = "steady"    # 稳健价值（9.2）
    BARGAIN = "bargain"  # 捡漏型（9.3）
    GROWTH = "growth"    # 高质量成长（9.4）
    MOAT = "moat"        # 护城河型（9.5）
