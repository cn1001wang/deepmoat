from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SwIndustryRead(BaseSchema):
    index_code: str = Field(..., alias="indexCode")
    industry_name: Optional[str] = Field(None, alias="industryName")
    parent_code: Optional[str] = Field(None, alias="parentCode")
    level: Optional[str] = None
    industry_code: Optional[str] = Field(None, alias="industryCode")
    is_pub: Optional[str] = Field(None, alias="isPub")
    src: Optional[str] = None
    class Config:
        orm_mode = True

class IndexMemberRead(BaseSchema):
    l1_code: str = Field(..., alias="l1Code")
    l1_name: Optional[str] = Field(None, alias="l1Name")
    l2_code: Optional[str] = Field(None, alias="l2Code")
    l2_name: Optional[str] = Field(None, alias="l2Name")
    l3_code: Optional[str] = Field(None, alias="l3Code")
    l3_name: Optional[str] = Field(None, alias="l3Name")
    ts_code: str = Field(..., alias="tsCode")
    name: Optional[str] = None
    in_date: Optional[str] = Field(None, alias="inDate")
    out_date: Optional[str] = Field(None, alias="outDate")
    is_new: Optional[str] = Field(None, alias="isNew")

class StockBasicRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    symbol: str
    name: str
    fullname: Optional[str] = None
    ennname: Optional[str] = None
    cnspell: Optional[str] = None
    area: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    curr_type: Optional[str] = Field(None, alias="currType")
    list_status: Optional[str] = Field(None, alias="listStatus")
    list_date: Optional[str] = Field(None, alias="listDate")
    delist_date: Optional[str] = Field(None, alias="delistDate")
    is_hs: Optional[str] = Field(None, alias="isHs")
    act_name: Optional[str] = Field(None, alias="actName")
    act_ent_type: Optional[str] = Field(None, alias="actEntType")

class StockCompanyRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    com_name: Optional[str] = Field(None, alias="comName")
    com_id: Optional[str] = Field(None, alias="comId")
    exchange: Optional[str] = None
    chairman: Optional[str] = None
    manager: Optional[str] = None
    secretary: Optional[str] = None
    reg_capital: Optional[float] = Field(None, alias="regCapital")
    setup_date: Optional[str] = Field(None, alias="setupDate")
    province: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    employees: Optional[int] = None


class TableRow(BaseModel):
    label: str
    key: str
    unit: str
    category: str
    values: List[Any]

class MetricsTable(BaseModel):
    periods: List[str]
    rows: List[TableRow]
