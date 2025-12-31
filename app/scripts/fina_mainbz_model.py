from sqlalchemy import Column, String, Float, Integer
from app.db.session import Base

class FinaMainbz(Base):
    __tablename__ = "fina_mainbz"

    ts_code = Column(String(100), primary_key=True, index=True, comment="TS代码")  # TS代码
    end_date = Column(String(100), primary_key=True, index=True, comment="报告期")  # 报告期
    bz_item = Column(String(100), comment="主营业务来源")  # 主营业务来源
    bz_sales = Column(Float, comment="主营业务收入(元)")  # 主营业务收入(元)
    bz_profit = Column(Float, comment="主营业务利润(元)")  # 主营业务利润(元)
    bz_cost = Column(Float, comment="主营业务成本(元)")  # 主营业务成本(元)
    curr_type = Column(String(100), comment="货币代码")  # 货币代码
    update_flag = Column(String(100), comment="是否更新")  # 是否更新
