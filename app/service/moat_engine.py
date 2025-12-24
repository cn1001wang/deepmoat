# 护城河算法逻辑 (Pandas 驱动)
import pandas as pd
from typing import Dict, Any

class MoatEngine:
    @staticmethod
    def build_metrics_table(income: pd.DataFrame, balance: pd.DataFrame, cash: pd.DataFrame) -> Dict[str, Any]:
        """
        这里放你原来的计算逻辑：_ensure_columns, _merge_frames, ROE 计算等。
        它是纯算法函数，不依赖数据库，方便测试。
        """
        # ... (保留你原来的 build_metrics_table 核心计算代码)
        return {"periods": periods, "rows": rows}