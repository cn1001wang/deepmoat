from app.models.models import Dividend
from sqlalchemy.orm import Session
from .base_bulk_upsert import bulk_upsert
import pandas as pd

def save_dividend(df: pd.DataFrame):
    # Tushare 接口返回的数据没有唯一 ID，且存在完全重复的业务数据（ts_code+end_date+ann_date+div_proc 都相同）
    # 因此我们不依赖数据库的 ON CONFLICT 唯一性约束来更新，而是采用 "先删后插" 的策略。
    # 
    # 策略：
    # 1. 找出 DataFrame 中涉及的 (ts_code, end_date) 组合
    # 2. 删除数据库中对应组合的所有记录
    # 3. 插入 DataFrame 中的新记录
    
    if df is None or df.empty:
        return

    from app.db.session import SessionLocal
    
    # 确保只包含模型字段
    from app.models.models import Dividend
    from sqlalchemy import inspect
    
    table_cols = {c.key for c in inspect(Dividend).mapper.column_attrs if c.key != 'id'} # 排除自增ID
    valid_cols = [c for c in df.columns if c in table_cols]
    if not valid_cols:
        return
    df = df[valid_cols] # type: ignore
    
    # 转换为字典列表
    records = df.where(pd.notnull(df), None).to_dict("records")
    if not records:
        return

    with SessionLocal() as db:
        # 提取需要更新的范围 (ts_code, end_date)
        # 注意：全量同步时可能涉及很多股票，这里如果全部 delete 可能效率低。
        # 但考虑到 fetch_dividend 是按 ts_code 抓取的（虽然我们在 worker 里改成了循环），
        # 每次 save_dividend 传入的 df 通常是单只股票的数据。
        
        # 获取当前批次涉及的 ts_code 列表
        ts_codes = df['ts_code'].unique().tolist()
        
        # 删除旧数据
        db.query(Dividend).filter(Dividend.ts_code.in_(ts_codes)).delete(synchronize_session=False)
        
        # 插入新数据
        db.bulk_insert_mappings(Dividend, records) # type: ignore
        db.commit()

def check_dividend_exists(db: Session, ts_code: str) -> bool:
    return db.query(Dividend).filter(Dividend.ts_code == ts_code).first() is not None

def get_dividend_by_ts_code(db: Session, ts_code: str) -> list[Dividend]:
    return db.query(Dividend).filter(Dividend.ts_code == ts_code).all()
