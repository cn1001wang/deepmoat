from sqlalchemy.orm import Session
from app.models.models import StockBasic
import pandas as pd

def save_stock_basic(db: Session, df: pd.DataFrame):
    """
    保存/更新股票基本信息
    注意：db 参数由外部(API或Worker)传入，此处不负责 commit() 以外的连接生命周期
    """
    try:
        for _, row in df.iterrows():
            # 使用模型解包，自动匹配列名，避免手动写几十行赋值
            # 过滤掉 row 中不在模型字段里的数据
            data = {k: v for k, v in row.to_dict().items() if hasattr(StockBasic, k)}
            
            obj = StockBasic(**data)
            db.merge(obj)  # merge 会根据主键自动判断是 Insert 还是 Update
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def get_stock_basic_all(db: Session):
    """
    获取所有股票基本信息
    """
    return db.query(StockBasic).all()

def get_stock_by_code(db: Session, ts_code: str):
    """
    根据代码获取单只股票
    """
    return db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()