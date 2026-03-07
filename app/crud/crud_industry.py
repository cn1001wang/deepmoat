from sqlalchemy.orm import Session
from app.models.models import SwIndustry
import pandas as pd
from app.models.models import IndexMember

def save_sw_industry(db: Session, df: pd.DataFrame):
    """将 Tushare 返回的 DataFrame 存入 PostgreSQL"""
    try:
        for _, row in df.iterrows():
            obj = SwIndustry(
                index_code=row["index_code"],
                industry_name=row["industry_name"],
                parent_code=row["parent_code"],
                level=row["level"],
                industry_code=row["industry_code"],
                is_pub=row["is_pub"],
                src=row["src"],
            )
            db.merge(obj)
        db.commit()
    except Exception:
        db.rollback()
        raise

def save_index_member(db: Session, df: pd.DataFrame):
    try:
        for _, row in df.iterrows():
            ts_code = row["ts_code"]
            l1_code = row["l1_code"]

            # 1. 删除该股票下，非当前 l1_code 的旧数据 (避免多条记录导致 API 报错，也避免 update 时的唯一性冲突)
            db.query(IndexMember).filter(
                IndexMember.ts_code == ts_code,
                IndexMember.l1_code != l1_code,
            ).delete(synchronize_session=False)

            # 2. 使用 merge 自动处理 Insert/Update (基于联合主键 l1_code + ts_code)
            obj = IndexMember(
                l1_code=l1_code,
                l1_name=row["l1_name"],
                l2_code=row["l2_code"],
                l2_name=row["l2_name"],
                l3_code=row["l3_code"],
                l3_name=row["l3_name"],
                ts_code=ts_code,
                name=row["name"],
                in_date=row["in_date"],
                out_date=row["out_date"],
                is_new=row["is_new"],
            )
            db.merge(obj)

        db.commit()
    except Exception:
        db.rollback()
        raise

def get_index_member(db: Session):
    return db.query(IndexMember).all()
def get_index_member_by_ts_code(db: Session, ts_code: str):
    """根据 ts_code 查询 IndexMember，返回列表（兼容接口校验）"""
    return db.query(IndexMember).filter(IndexMember.ts_code == ts_code).one_or_none()

def get_sw_industry(db: Session):
    return db.query(SwIndustry).all()
