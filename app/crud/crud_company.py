from sqlalchemy.orm import Session
from app.models.models import StockCompany
import pandas as pd
import math

# ------------------------
# 内部工具函数 (保持私有)
# ------------------------

def _clean_val(v, func):
    """通用清理函数，处理 NaN 和 None"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        return func(v)
    except (ValueError, TypeError):
        return None

# ------------------------
# 核心 CRUD 逻辑
# ------------------------

def save_stock_company(db: Session, df: pd.DataFrame):
    """
    保存/更新公司信息
    """
    try:
        for _, row in df.iterrows():
            # 1. 提取 DataFrame 中的数据并清理特定字段
            row_data = row.to_dict()
            
            # 手动处理需要类型转换的字段
            row_data["reg_capital"] = _clean_val(row_data.get("reg_capital"), float)
            row_data["employees"] = _clean_val(row_data.get("employees"), int)

            # 2. 动态构建模型对象 (只匹配模型中存在的字段)
            valid_data = {k: v for k, v in row_data.items() if hasattr(StockCompany, k)}
            obj = StockCompany(**valid_data)
            
            db.merge(obj)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def get_all_listed_companies_info(db: Session):
    """
    获取非深交所上市公司的代码和成立日期
    """
    rows = db.query(
        StockCompany.ts_code,
        StockCompany.setup_date
    ).filter(StockCompany.exchange != "SZSE").all()

    # 显式转成 tuple[str, str]
    return [(r.ts_code, r.setup_date) for r in rows]

def get_stock_companies(db: Session):
    """
    获取所有公司对象
    """
    return db.query(StockCompany).all()