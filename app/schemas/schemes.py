from pydantic import BaseModel
from typing import Optional

# 基础模型
class SwIndustryBase(BaseModel):
    industry_name: str
    parent_code: Optional[str] = None
    level: Optional[str] = None
    industry_code: Optional[str] = None
    is_pub: Optional[str] = None
    src: Optional[str] = None

    class Config:
        from_attributes = True # 允许从 SQLAlchemy 对象读取数据

# 创建时需要的字段
class SwIndustryCreate(SwIndustryBase):
    index_code: str

# 读取时返回的字段
class SwIndustryResponse(SwIndustryBase):
    index_code: str