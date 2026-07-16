"""AI 估值报告落盘。"""
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.crud.crud_stock import get_stock_by_code


def save_valuation_report(ts_code: str, content: str, db: Session) -> str:
    """将报告内容写入 outputs/reports/<symbol>_<name>/ 下，返回文件路径。"""
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
