from common.database import SessionLocal
from common.models import SwIndustry
import pandas as pd
from common.models import IndexMember


def save_sw_industry(df: pd.DataFrame):
    """将 Tushare 返回的 DataFrame 存入 PostgreSQL"""

    session = SessionLocal()

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

            session.merge(obj)  # merge 支持更新/插入
        session.commit()
    except Exception as e:
        session.rollback()
        print("写入错误：", e)
        raise
    finally:
        session.close()

def save_index_member(df: pd.DataFrame):
    """将 Tushare 返回的 DataFrame 存入 PostgreSQL"""

    session = SessionLocal()

    try:
        for _, row in df.iterrows():
            # 先查询是否存在同 ts_code 的记录
            existing = session.query(IndexMember).filter_by(ts_code=row["ts_code"]).first()
            if existing:
                # 存在则更新
                existing.l1_code = row["l1_code"]
                existing.l1_name = row["l1_name"]
                existing.l2_code = row["l2_code"]
                existing.l2_name = row["l2_name"]
                existing.l3_code = row["l3_code"]
                existing.l3_name = row["l3_name"]
                existing.name = row["name"]
                existing.in_date = row["in_date"]
                existing.out_date = row["out_date"]
                existing.is_new = row["is_new"]
            else:
                # 不存在则新增
                obj = IndexMember(
                    l1_code=row["l1_code"],
                    l1_name=row["l1_name"],
                    l2_code=row["l2_code"],
                    l2_name=row["l2_name"],
                    l3_code=row["l3_code"],
                    l3_name=row["l3_name"],
                    ts_code=row["ts_code"],
                    name=row["name"],
                    in_date=row["in_date"],
                    out_date=row["out_date"],
                    is_new=row["is_new"],
                )
                session.add(obj)
        session.commit()
    except Exception as e:
        session.rollback()
        print("写入错误：", e)
        raise
    finally:
        session.close()

def get_index_member():
    session = SessionLocal()
    try:
        data = session.query(IndexMember).all()
    except Exception as e:
        print("查询错误：", e)
        raise
    finally:
        session.close()
    return data


def get_sw_industry():
    
    session = SessionLocal()
    try:
        industry = session.query(SwIndustry).all()
    except Exception as e:
        print("查询错误：", e)
        raise
    finally:
        session.close()
    return industry