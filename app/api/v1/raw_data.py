"""
原始财务 & 基础数据 API
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stock_shcemes import SwIndustryRead, StockBasicRead, IndexMemberRead, StockCompanyRead, MetricsTable
from app.service.finance_metrics import build_metrics_table
from app.crud.crud_stock import get_stock_basic_all
from app.crud.crud_company import get_stock_companies
from app.crud.crud_industry import get_sw_industry, get_index_member
from app.utils.api_utils import ok, ResponseOk

router = APIRouter(
    tags=["raw_data"]
)


@router.get("/finance/table", response_model=ResponseOk[MetricsTable])
def get_finance_table_api(
    ts_code: str = Query(..., description="股票代码，如 000001.SZ"),
    years: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    try:
        data = build_metrics_table(ts_code, years)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not data["periods"]:
        raise HTTPException(status_code=404, detail="未找到财报数据")

    return ok(data)


@router.get("/sw_industry",  response_model=ResponseOk[list[SwIndustryRead]])
def get_sw_industry_api(db: Session = Depends(get_db)):
    return ok(get_sw_industry(db))


@router.get("/stock_basic_all",  response_model=ResponseOk[list[StockBasicRead]])
def get_stock_basic_all_api(db: Session = Depends(get_db)):
    return ok(get_stock_basic_all(db))


@router.get("/index_member",  response_model=ResponseOk[list[IndexMemberRead]])
def get_index_member_api(db: Session = Depends(get_db)):
    return ok(get_index_member(db))


@router.get("/company",  response_model=ResponseOk[list[StockCompanyRead]])
def get_company_api(db: Session = Depends(get_db)):
    return ok(get_stock_companies(db))
