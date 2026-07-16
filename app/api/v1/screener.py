from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.service.screener_service import run_screener, check_risk

router = APIRouter(prefix="/screener", tags=["screener"])


class ScreenerParams(BaseModel):
    min_roe: Optional[float] = None
    max_debt_ratio: Optional[float] = None
    min_cashflow_ratio: Optional[float] = None
    max_goodwill_ratio: Optional[float] = None
    min_dividend_yield: Optional[float] = None


class ScreenerRequest(BaseModel):
    strategy: str = "稳健价值型"
    params: Optional[ScreenerParams] = None
    years: int = 5


@router.post("/run")
def screener_run(req: ScreenerRequest, db: Session = Depends(get_db)):
    result = run_screener(
        db,
        strategy=req.strategy,
        params=req.params.model_dump(exclude_none=True) if req.params else {},
        years=req.years,
    )
    return {"code": 200, "data": result, "message": "ok"}


@router.get("/risk-check")
def screener_risk_check(ts_code: str, db: Session = Depends(get_db)):
    result = check_risk(db, ts_code)
    return {"code": 200, "data": result, "message": "ok"}
