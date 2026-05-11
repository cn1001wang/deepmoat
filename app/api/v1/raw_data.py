"""
原始财务 & 基础数据 API
"""
import math

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import or_
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import BalanceSheet, CashFlow, DailyBasic, FinaIndicator, FinaMainbz, Income
from app.schemas.stock_shcemes import SwIndustryRead, StockBasicRead, IndexMemberRead, StockCompanyRead, MetricsTable
from app.schemas.finance_schemes import FinaIndicatorRead, FinaAuditRead, DailyBasicRead
from app.service.finance_metrics import build_metrics_table
from app.crud.crud_stock import get_stock_basic_all, get_stock_by_code
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


def _safe_ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    result = float(numerator) / float(denominator) * 100
    return result if math.isfinite(result) else None


def _safe_sum(*values):
    total = 0.0
    has_value = False
    for value in values:
        if value is None:
            continue
        number = float(value)
        if not math.isfinite(number):
            continue
        total += number
        has_value = True
    return total if has_value else None


BALANCESHEET_CARD_COLUMNS = {
    "loanto_oth_bank_fi": "FLOAT",
    "deriv_assets": "FLOAT",
    "pur_resale_fa": "FLOAT",
    "fair_value_fin_assets": "FLOAT",
    "cost_fin_assets": "FLOAT",
    "receiv_financing": "FLOAT",
    "accounts_receiv_bill": "FLOAT",
    "acc_receivable": "FLOAT",
    "premium_receiv": "FLOAT",
    "reinsur_receiv": "FLOAT",
    "reinsur_res_receiv": "FLOAT",
    "debt_invest": "FLOAT",
    "oth_debt_invest": "FLOAT",
    "oth_eq_invest": "FLOAT",
    "oth_illiq_fin_assets": "FLOAT",
    "lt_rec": "FLOAT",
    "cip_total": "FLOAT",
    "const_materials": "FLOAT",
    "fixed_assets_disp": "FLOAT",
    "produc_bio_assets": "FLOAT",
    "oil_and_gas_assets": "FLOAT",
    "r_and_d": "FLOAT",
    "lt_amor_exp": "FLOAT",
    "non_cur_liab_due_1y": "FLOAT",
    "cb_borr": "FLOAT",
    "depos_ib_deposits": "FLOAT",
    "loan_oth_bank": "FLOAT",
    "trading_fl": "FLOAT",
    "accounts_payable": "FLOAT",
    "contract_liab": "FLOAT",
    "payroll_payable": "FLOAT",
    "lt_payable": "FLOAT",
    "specific_payables": "FLOAT",
    "estimated_liab": "FLOAT",
}


def _ensure_balancesheet_card_columns(db: Session):
    bind = db.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("balancesheet")}
    missing_columns = [name for name in BALANCESHEET_CARD_COLUMNS if name not in existing_columns]
    if not missing_columns:
        return
    for name in missing_columns:
        db.execute(text(f"ALTER TABLE balancesheet ADD COLUMN {name} {BALANCESHEET_CARD_COLUMNS[name]}"))
    db.commit()


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
                    "netProfitMargin": [None] * years,
                    "adminExpenseRatio": [None] * years,
                    "salesExpenseRatio": [None] * years,
                    "rdExpenseRatio": [None] * years,
                    "financeExpenseRatio": [None] * years,
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
            FinaIndicator.netprofit_margin,
            FinaIndicator.adminexp_of_gr,
            FinaIndicator.saleexp_to_gr,
            FinaIndicator.finaexp_of_gr,
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
        index = year - year_list[0]
        metrics["grossMargin"][index] = _safe_float(row.grossprofit_margin)
        metrics["netProfitMargin"][index] = _safe_float(row.netprofit_margin)
        metrics["adminExpenseRatio"][index] = _safe_float(row.adminexp_of_gr)
        metrics["salesExpenseRatio"][index] = _safe_float(row.saleexp_to_gr)
        metrics["financeExpenseRatio"][index] = _safe_float(row.finaexp_of_gr)

    rd_rows = (
        db.query(
            Income.ts_code,
            Income.end_date,
            Income.ann_date,
            Income.report_type,
            Income.revenue,
            Income.total_revenue,
            Income.rd_exp,
        )
        .filter(Income.end_date >= start_end_date, Income.end_date <= end_end_date)
        .filter(Income.end_date.like("%1231"))
        .order_by(Income.ts_code, Income.end_date, Income.ann_date.desc(), Income.report_type)
        .all()
    )
    seen_rd = set()
    for row in rd_rows:
        year = _annual_year(row.end_date)
        if year not in year_list:
            continue
        key = (row.ts_code, year)
        if key in seen_rd:
            continue
        seen_rd.add(key)
        metrics = ensure_row(row.ts_code)
        revenue = row.revenue if row.revenue is not None else row.total_revenue
        metrics["rdExpenseRatio"][year - year_list[0]] = _safe_ratio(row.rd_exp, revenue)

    return ok(list(result.values()))


@router.get("/sw_industry",  response_model=ResponseOk[list[SwIndustryRead]])
def get_sw_industry_api(db: Session = Depends(get_db)):
    return ok(get_sw_industry(db))


@router.get("/stock_basic_all",  response_model=ResponseOk[list[StockBasicRead]])
def get_stock_basic_all_api(db: Session = Depends(get_db)):
    return ok(get_stock_basic_all(db))


@router.get("/stock_basic", response_model=ResponseOk[StockBasicRead])
def get_stock_basic_api(
    ts_code: str = Query(..., description="股票代码，如 000001.SZ"),
    db: Session = Depends(get_db),
):
    stock = get_stock_by_code(db, ts_code)
    if not stock:
        raise HTTPException(status_code=404, detail="未找到股票基础资料")
    return ok(stock)


def _latest_by_period(rows):
    result = {}
    for row in rows:
        current = result.get(row.end_date)
        if current is None or (row.ann_date or "") > (current.ann_date or ""):
            result[row.end_date] = row
    return [result[key] for key in sorted(result.keys())]


def _format_period(end_date: str | None):
    if not end_date or len(end_date) != 8:
        return end_date
    return f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"


def _mainbz_point(row):
    return {
        "period": _format_period(row.end_date),
        "type": row.type,
        "item": row.bz_item,
        "sales": _safe_float(row.bz_sales),
        "profit": _safe_float(row.bz_profit),
        "cost": _safe_float(row.bz_cost),
    }


def _valuation_date(*rows):
    dates = [row.ann_date for row in rows if row is not None and row.ann_date]
    return max(dates) if dates else None


def _valuation_at_or_before(db: Session, ts_code: str, trade_date: str | None):
    if not trade_date:
        return None
    return (
        db.query(DailyBasic)
        .filter(DailyBasic.ts_code == ts_code, DailyBasic.trade_date <= trade_date)
        .order_by(DailyBasic.trade_date.desc())
        .first()
    )


@router.get("/finance/card")
def get_finance_card_api(
    ts_code: str = Query(..., description="股票代码，如 000001.SZ"),
    years: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    财务小卡片本地只读数据。
    不从 Tushare 拉取，不自动补数；缺失模块由前端提示同步命令。
    """
    _ensure_balancesheet_card_columns(db)

    stock = get_stock_by_code(db, ts_code)
    industry = get_index_member_by_ts_code(db, ts_code)

    income_rows = _latest_by_period(
        db.query(Income)
        .filter(Income.ts_code == ts_code)
        .order_by(Income.end_date.desc(), Income.ann_date.desc())
        .limit(years * 4)
        .all()
    )
    balance_rows = _latest_by_period(
        db.query(BalanceSheet)
        .filter(BalanceSheet.ts_code == ts_code)
        .order_by(BalanceSheet.end_date.desc(), BalanceSheet.ann_date.desc())
        .limit(years * 4)
        .all()
    )
    cashflow_rows = _latest_by_period(
        db.query(CashFlow)
        .filter(CashFlow.ts_code == ts_code)
        .order_by(CashFlow.end_date.desc(), CashFlow.ann_date.desc())
        .limit(years * 4)
        .all()
    )
    indicator_rows = _latest_by_period(
        db.query(FinaIndicator)
        .filter(FinaIndicator.ts_code == ts_code)
        .order_by(FinaIndicator.end_date.desc(), FinaIndicator.ann_date.desc())
        .limit(years * 4)
        .all()
    )
    daily_rows = (
        db.query(DailyBasic)
        .filter(DailyBasic.ts_code == ts_code)
        .order_by(DailyBasic.trade_date.desc())
        .limit(260)
        .all()
    )
    latest_mainbz_period = (
        db.query(FinaMainbz.end_date)
        .filter(FinaMainbz.ts_code == ts_code, FinaMainbz.type == "P")
        .order_by(FinaMainbz.end_date.desc())
        .limit(1)
        .scalar()
    )
    mainbz_rows = []
    if latest_mainbz_period:
        mainbz_rows = (
            db.query(FinaMainbz)
            .filter(
                FinaMainbz.ts_code == ts_code,
                FinaMainbz.type == "P",
                FinaMainbz.end_date == latest_mainbz_period,
            )
            .order_by(FinaMainbz.bz_sales.desc().nullslast())
            .all()
        )

    periods = sorted({
        row.end_date
        for row in [*income_rows, *balance_rows, *cashflow_rows, *indicator_rows]
        if row.end_date
    })
    income_map = {row.end_date: row for row in income_rows}
    balance_map = {row.end_date: row for row in balance_rows}
    cashflow_map = {row.end_date: row for row in cashflow_rows}
    indicator_map = {row.end_date: row for row in indicator_rows}

    finance_series = []
    for period in periods:
        income = income_map.get(period)
        balance = balance_map.get(period)
        cashflow = cashflow_map.get(period)
        indicator = indicator_map.get(period)
        valuation = _valuation_at_or_before(
            db,
            ts_code,
            _valuation_date(income, balance, cashflow, indicator) or period,
        )
        fixed_assets = _safe_sum(
            balance.fix_assets,
            balance.cip_total if balance.cip_total is not None else balance.cip,
            balance.const_materials,
            balance.fixed_assets_disp,
            balance.produc_bio_assets,
            balance.oil_and_gas_assets,
        ) if balance else None
        financial_assets = _safe_sum(
            balance.trad_asset,
            balance.loanto_oth_bank_fi,
            balance.deriv_assets,
            balance.pur_resale_fa,
            balance.fa_avail_for_sale,
            balance.htm_invest,
            balance.debt_invest,
            balance.oth_debt_invest,
            balance.oth_eq_invest,
            balance.oth_illiq_fin_assets,
            balance.fair_value_fin_assets,
            balance.cost_fin_assets,
            balance.time_deposits,
        ) if balance else None
        receivables = _safe_sum(
            balance.accounts_receiv_bill,
            balance.oth_receiv,
            balance.div_receiv,
            balance.int_receiv,
            balance.premium_receiv,
            balance.reinsur_receiv,
            balance.reinsur_res_receiv,
            balance.receiv_financing,
        ) if balance else None
        prepaid_assets = _safe_sum(balance.prepayment) if balance else None
        intangible_assets = _safe_sum(balance.intan_assets, balance.r_and_d, balance.lt_amor_exp) if balance else None
        goodwill = _safe_float(balance.goodwill) if balance else None
        interest_bearing_debt = _safe_sum(
            balance.st_borr,
            balance.lt_borr,
            balance.non_cur_liab_due_1y,
            balance.bond_payable,
            balance.cb_borr,
            balance.depos_ib_deposits,
            balance.loan_oth_bank,
            balance.trading_fl,
        ) if balance else None
        payables = _safe_sum(balance.notes_payable, balance.accounts_payable, balance.acct_payable) if balance else None
        contract_liabilities = _safe_sum(balance.adv_receipts, balance.contract_liab) if balance else None
        employee_tax_payables = _safe_sum(balance.payroll_payable, balance.taxes_payable) if balance else None
        other_liabilities = None
        if balance and balance.total_liab is not None:
            known_liabilities = _safe_sum(
                interest_bearing_debt,
                payables,
                contract_liabilities,
                employee_tax_payables,
            )
            other_liabilities = max(balance.total_liab - (known_liabilities or 0), 0)
        parent_equity = _safe_float(balance.total_hldr_eqy_exc_min_int if balance else None)
        minority_equity = _safe_float(balance.minority_int if balance else None)
        known_assets = _safe_sum(
            balance.money_cap if balance else None,
            financial_assets,
            fixed_assets,
            balance.invest_real_estate if balance else None,
            balance.lt_eqt_invest if balance else None,
            receivables,
            prepaid_assets,
            balance.inventories if balance else None,
            intangible_assets,
            goodwill,
        )
        other_assets = None
        if balance and balance.total_assets is not None:
            other_assets = balance.total_assets - (known_assets or 0)
        finance_series.append({
            "period": _format_period(period),
            "revenue": _safe_float(income.revenue if income and income.revenue is not None else income.total_revenue if income else None),
            "netProfit": _safe_float(income.n_income_attr_p if income and income.n_income_attr_p is not None else income.n_income if income else None),
            "operatingCashFlow": _safe_float(cashflow.n_cashflow_act if cashflow else None),
            "grossMargin": _safe_float(indicator.grossprofit_margin if indicator else None),
            "netProfitMargin": _safe_float(indicator.netprofit_margin if indicator else None),
            "roe": _safe_float(indicator.roe if indicator else None),
            "totalAssets": _safe_float(balance.total_assets if balance else None),
            "totalLiab": _safe_float(balance.total_liab if balance else None),
            "moneyCap": _safe_float(balance.money_cap if balance else None),
            "interestDebt": _safe_float(indicator.interestdebt if indicator else None),
            "valuationDate": _format_period(valuation.trade_date) if valuation else None,
            "close": _safe_float(valuation.close if valuation else None),
            "pe": _safe_float(valuation.pe_ttm if valuation and valuation.pe_ttm is not None else valuation.pe if valuation else None),
            "pb": _safe_float(valuation.pb if valuation else None),
            "fixedAssets": _safe_float(fixed_assets),
            "financialAssets": _safe_float(financial_assets),
            "investRealEstate": _safe_float(balance.invest_real_estate if balance else None),
            "longEquityInvestment": _safe_float(balance.lt_eqt_invest if balance else None),
            "receivables": _safe_float(receivables),
            "prepaidAssets": _safe_float(prepaid_assets),
            "inventories": _safe_float(balance.inventories if balance else None),
            "intangibleAssets": _safe_float(intangible_assets),
            "goodwill": _safe_float(goodwill),
            "otherAssets": _safe_float(other_assets),
            "interestBearingDebt": _safe_float(interest_bearing_debt),
            "payables": _safe_float(payables),
            "contractLiabilities": _safe_float(contract_liabilities),
            "employeeTaxPayables": _safe_float(employee_tax_payables),
            "otherLiabilities": _safe_float(other_liabilities),
            "parentEquity": _safe_float(parent_equity),
            "minorityEquity": _safe_float(minority_equity),
        })

    valuation_series = [
        {
            "tradeDate": _format_period(row.trade_date),
            "close": _safe_float(row.close),
            "pe": _safe_float(row.pe_ttm if row.pe_ttm is not None else row.pe),
            "pb": _safe_float(row.pb),
        }
        for row in reversed(daily_rows)
    ]

    missing_modules = []
    if not stock:
        missing_modules.append("stock_basic")
    if not income_rows or not balance_rows or not cashflow_rows:
        missing_modules.append("finance")
    if not indicator_rows:
        missing_modules.append("fina_indicator")
    if not daily_rows:
        missing_modules.append("daily_basic")
    if not mainbz_rows:
        missing_modules.append("fina_mainbz")

    return ok({
        "tsCode": ts_code,
        "stock": stock.to_dict() if stock else None,
        "industry": industry.to_dict() if industry else None,
        "financeSeries": finance_series,
        "valuationSeries": valuation_series,
        "mainBusinessSeries": [_mainbz_point(row) for row in mainbz_rows],
        "missingModules": missing_modules,
    })


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
