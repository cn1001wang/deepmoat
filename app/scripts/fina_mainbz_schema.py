from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class FinaMainbzRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")  # TS代码
    end_date: str = Field(..., alias="endDate")  # 报告期
    bz_item: Optional[str] = Field(None, alias="bzItem")  # 主营业务来源
    bz_sales: Optional[float] = Field(None, alias="bzSales")  # 主营业务收入(元)
    bz_profit: Optional[float] = Field(None, alias="bzProfit")  # 主营业务利润(元)
    bz_cost: Optional[float] = Field(None, alias="bzCost")  # 主营业务成本(元)
    curr_type: Optional[str] = Field(None, alias="currType")  # 货币代码
    update_flag: Optional[str] = Field(None, alias="updateFlag")  # 是否更新
