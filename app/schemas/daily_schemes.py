from pydantic import BaseModel
from typing import Optional

class DailyBasicSchema(BaseModel):
    ts_code: str
    trade_date: str

    close: Optional[float] = None

    turnover_rate: Optional[float] = None
    turnover_rate_f: Optional[float] = None
    volume_ratio: Optional[float] = None

    pe: Optional[float] = None
    pe_ttm: Optional[float] = None

    pb: Optional[float] = None

    ps: Optional[float] = None
    ps_ttm: Optional[float] = None

    dv_ratio: Optional[float] = None
    dv_ttm: Optional[float] = None

    total_share: Optional[float] = None
    float_share: Optional[float] = None
    free_share: Optional[float] = None

    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None
