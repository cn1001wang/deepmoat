from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DividendRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")  # TS代码
    end_date: str = Field(..., alias="endDate")  # 分红年度
    ann_date: str = Field(..., alias="annDate")  # 预案公告日
    div_proc: Optional[str] = Field(None, alias="divProc")  # 实施进度
    stk_div: Optional[float] = Field(None, alias="stkDiv")  # 每股送转
    stk_bo_rate: Optional[float] = Field(None, alias="stkBoRate")  # 每股送股比例
    stk_co_rate: Optional[float] = Field(None, alias="stkCoRate")  # 每股转增比例
    cash_div: Optional[float] = Field(None, alias="cashDiv")  # 每股分红（税后）
    cash_div_tax: Optional[float] = Field(None, alias="cashDivTax")  # 每股分红（税前）
    record_date: Optional[str] = Field(None, alias="recordDate")  # 股权登记日
    ex_date: Optional[str] = Field(None, alias="exDate")  # 除权除息日
    pay_date: Optional[str] = Field(None, alias="payDate")  # 派息日
    div_listdate: Optional[str] = Field(None, alias="divListdate")  # 红股上市日
    imp_ann_date: Optional[str] = Field(None, alias="impAnnDate")  # 实施公告日
    base_date: Optional[str] = Field(None, alias="baseDate")  # 基准日
    base_share: Optional[float] = Field(None, alias="baseShare")  # 基准股本（万）
