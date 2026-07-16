from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.service.ai import AnalysisMode, generate_valuation, save_valuation_report

router = APIRouter(prefix="/ai", tags=["ai"])


class ValuationRequest(BaseModel):
    ts_code: str
    # 评分模式（投资体系 v2 第九章）：None/auto 由 AI 按 9.1 决策树自判
    mode: Optional[AnalysisMode] = None


class ValuationSaveRequest(BaseModel):
    ts_code: str
    content: str


@router.post("/valuation")
async def ai_valuation(req: ValuationRequest, db: Session = Depends(get_db)):
    result = await generate_valuation(req.ts_code, db, req.mode)
    return {"code": 200, "data": result, "message": "ok"}


@router.post("/valuation/save")
def ai_valuation_save(req: ValuationSaveRequest, db: Session = Depends(get_db)):
    path = save_valuation_report(req.ts_code, req.content, db)
    return {"code": 200, "data": {"path": path}, "message": "ok"}
