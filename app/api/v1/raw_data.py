"""
原始财务 & 基础数据 API
"""
import math

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import CashFlow, FinaIndicator, Income
from app.schemas.stock_shcemes import SwIndustryRead, StockBasicRead, IndexMemberRead, StockCompanyRead, MetricsTable
from app.schemas.finance_schemes import FinaIndicatorRead, FinaAuditRead, DailyBasicRead
from app.service.finance_metrics import build_metrics_table
from app.crud.crud_stock import get_stock_basic_all
from app.crud.crud_company import get_stock_companies
from app.crud.crud_industry import get_sw_industry, get_index_member, get_index_member_by_ts_code
from app.utils.api_utils import ok, ResponseOk
from app.crud.crud_fina_indicator import get_fina_indicator
from app.crud.crud_fina_audit import get_fina_audit
from app.crud.crud_daily import get_daily_basic

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


def _annual_year(end_date: str | None) -> int | None:
    if not end_date or len(end_date) < 4:
        return None
    try:
        return int(end_date[:4])
    except ValueError:
        return None


def _safe_float(value):
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


@router.get("/annual_metric_trends")
def get_annual_metric_trends_api(
    years: int = Query(10, ge=1, le=20),
    latest_year: int | None = Query(None, ge=1990, le=2100),
    db: Session = Depends(get_db)
):
    """
    股票列表页使用的近 N 年年报趋势。
    数据口径：仅取 12-31 年报；缺失年份保留为 None，由前端渲染占位符。
    """
    latest_end_date = f"{latest_year}1231" if latest_year else None
    if latest_end_date is None:
        latest_end_date = max(
            db.query(Income.end_date)
            .filter(Income.end_date.like("%1231"))
            .order_by(Income.end_date.desc())
            .limit(1)
            .scalar()
            or "",
            db.query(CashFlow.end_date)
            .filter(CashFlow.end_date.like("%1231"))
            .order_by(CashFlow.end_date.desc())
            .limit(1)
            .scalar()
            or "",
            db.query(FinaIndicator.end_date)
            .filter(FinaIndicator.end_date.like("%1231"))
            .order_by(FinaIndicator.end_date.desc())
            .limit(1)
            .scalar()
            or "",
        )

    resolved_latest_year = _annual_year(latest_end_date)
    if resolved_latest_year is None:
        return ok([])

    year_list = list(range(resolved_latest_year - years + 1, resolved_latest_year + 1))
    start_end_date = f"{year_list[0]}1231"
    end_end_date = f"{year_list[-1]}1231"

    result: dict[str, dict] = {}

    def ensure_row(ts_code: str):
        if ts_code not in result:
            result[ts_code] = {
                "tsCode": ts_code,
                "annualMetrics": {
                    "years": year_list,
                    "revenue": [None] * years,
                    "netProfit": [None] * years,
                    "operatingCashFlow": [None] * years,
                    "grossMargin": [None] * years,
                },
            }
        return result[ts_code]["annualMetrics"]

    income_rows = (
        db.query(
            Income.ts_code,
            Income.end_date,
            Income.ann_date,
            Income.report_type,
            Income.revenue,
            Income.total_revenue,
            Income.n_income_attr_p,
            Income.n_income,
        )
        .filter(Income.end_date >= start_end_date, Income.end_date <= end_end_date)
        .filter(Income.end_date.like("%1231"))
        .order_by(Income.ts_code, Income.end_date, Income.ann_date.desc(), Income.report_type)
        .all()
    )
    seen_income = set()
    for row in income_rows:
        year = _annual_year(row.end_date)
        if year not in year_list:
            continue
        key = (row.ts_code, year)
        if key in seen_income:
            continue
        seen_income.add(key)
        metrics = ensure_row(row.ts_code)
        index = year - year_list[0]
        metrics["revenue"][index] = _safe_float(row.revenue if row.revenue is not None else row.total_revenue)
        metrics["netProfit"][index] = _safe_float(row.n_income_attr_p if row.n_income_attr_p is not None else row.n_income)

    cash_rows = (
        db.query(
            CashFlow.ts_code,
            CashFlow.end_date,
            CashFlow.ann_date,
            CashFlow.report_type,
            CashFlow.n_cashflow_act,
        )
        .filter(CashFlow.end_date >= start_end_date, CashFlow.end_date <= end_end_date)
        .filter(CashFlow.end_date.like("%1231"))
        .order_by(CashFlow.ts_code, CashFlow.end_date, CashFlow.ann_date.desc(), CashFlow.report_type)
        .all()
    )
    seen_cash = set()
    for row in cash_rows:
        year = _annual_year(row.end_date)
        if year not in year_list:
            continue
        key = (row.ts_code, year)
        if key in seen_cash:
            continue
        seen_cash.add(key)
        metrics = ensure_row(row.ts_code)
        metrics["operatingCashFlow"][year - year_list[0]] = _safe_float(row.n_cashflow_act)

    indicator_rows = (
        db.query(
            FinaIndicator.ts_code,
            FinaIndicator.end_date,
            FinaIndicator.ann_date,
            FinaIndicator.grossprofit_margin,
        )
        .filter(FinaIndicator.end_date >= start_end_date, FinaIndicator.end_date <= end_end_date)
        .filter(FinaIndicator.end_date.like("%1231"))
        .filter(or_(FinaIndicator.grossprofit_margin.is_(None), FinaIndicator.grossprofit_margin <= 1000))
        .order_by(FinaIndicator.ts_code, FinaIndicator.end_date, FinaIndicator.ann_date.desc())
        .all()
    )
    seen_indicator = set()
    for row in indicator_rows:
        year = _annual_year(row.end_date)
        if year not in year_list:
            continue
        key = (row.ts_code, year)
        if key in seen_indicator:
            continue
        seen_indicator.add(key)
        metrics = ensure_row(row.ts_code)
        metrics["grossMargin"][year - year_list[0]] = _safe_float(row.grossprofit_margin)

    return ok(list(result.values()))


@router.get("/sw_industry",  response_model=ResponseOk[list[SwIndustryRead]])
def get_sw_industry_api(db: Session = Depends(get_db)):
    return ok(get_sw_industry(db))


@router.get("/stock_basic_all",  response_model=ResponseOk[list[StockBasicRead]])
def get_stock_basic_all_api(db: Session = Depends(get_db)):
    return ok(get_stock_basic_all(db))


@router.get("/index_member",  response_model=ResponseOk[list[IndexMemberRead]])
def get_index_member_api(db: Session = Depends(get_db)):
    return ok(get_index_member(db))

@router.get("/index_member_by_ts_code",  response_model=ResponseOk[IndexMemberRead])
def get_index_member_by_ts_code_api(ts_code: str = Query(..., description="指数代码，如 000001.SH"), db: Session = Depends(get_db)):
    return ok(get_index_member_by_ts_code(db, ts_code))

@router.get("/company",  response_model=ResponseOk[list[StockCompanyRead]])
def get_company_api(db: Session = Depends(get_db)):
    return ok(get_stock_companies(db))

@router.get("/fina_indicator",  response_model=ResponseOk[list[FinaIndicatorRead]])
def get_fina_indicator_api(ann_date: str = Query(None, description="公告日期，如 20230101"), end_date: str = Query(None, description="报告期，如 20231231"), ts_code: str = Query(None, description="股票代码，如 000001.SZ"), db: Session = Depends(get_db)):
    return ok(get_fina_indicator(ann_date, end_date, ts_code, db))

@router.get("/fina_audit", response_model=ResponseOk[list[FinaAuditRead]])
def get_fina_audit_api(ts_code: str = Query(..., description="股票代码，如 000001.SZ"), db: Session = Depends(get_db)):
    return ok(get_fina_audit(ts_code, db))

@router.get("/daily_basic",  response_model=ResponseOk[list[DailyBasicRead]])
def get_daily_basic_api(trade_date: str = Query(None, description="交易日期，如 20230101"), ts_code: str = Query(None, description="股票代码，如 000001.SZ"), db: Session = Depends(get_db)):
    return ok(get_daily_basic( trade_date, ts_code, db))
