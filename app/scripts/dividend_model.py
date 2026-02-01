from sqlalchemy import Column, String, Float, Integer
from app.db.session import Base

class Dividend(Base):
    __tablename__ = "dividend"

    ts_code = Column(String(100), primary_key=True, index=True, comment="TS代码")  # TS代码
    end_date = Column(String(100), primary_key=True, index=True, comment="分红年度")  # 分红年度
    ann_date = Column(String(100), primary_key=True, index=True, comment="预案公告日")  # 预案公告日
    div_proc = Column(String(100), comment="实施进度")  # 实施进度
    stk_div = Column(Float, comment="每股送转")  # 每股送转
    stk_bo_rate = Column(Float, comment="每股送股比例")  # 每股送股比例
    stk_co_rate = Column(Float, comment="每股转增比例")  # 每股转增比例
    cash_div = Column(Float, comment="每股分红（税后）")  # 每股分红（税后）
    cash_div_tax = Column(Float, comment="每股分红（税前）")  # 每股分红（税前）
    record_date = Column(String(100), comment="股权登记日")  # 股权登记日
    ex_date = Column(String(100), comment="除权除息日")  # 除权除息日
    pay_date = Column(String(100), comment="派息日")  # 派息日
    div_listdate = Column(String(100), comment="红股上市日")  # 红股上市日
    imp_ann_date = Column(String(100), comment="实施公告日")  # 实施公告日
    base_date = Column(String(100), comment="基准日")  # 基准日
    base_share = Column(Float, comment="基准股本（万）")  # 基准股本（万）
