from sqlalchemy.orm import Session
from app.models import StockBasic
import pandas as pd

def save_stock_basic(db: Session, df: pd.DataFrame):
    """底层抓取任务使用：将 DataFrame 写入数据库"""
    for _, row in df.iterrows():
        obj = StockBasic(**row.to_dict()) # 假设字段名匹配
        db.merge(obj)
    db.commit()

def get_stock_basic_all(db: Session):
    """中间层：直接读取原始股票数据"""
    return db.query(StockBasic).all()