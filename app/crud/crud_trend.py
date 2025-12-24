# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Income, BalanceSheet, CashFlow, StockBasic

def get_stock_basic(db: Session, ts_code: str):
    """获取股票基本信息"""
    return db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()

def get_financial_history(db: Session, ts_code: str, limit: int = 12):
    """
    获取指定股票最近 N 个报告期的财务数据。
    同时联合查询利润表、资产负债表、现金流量表。
    注意：这里假设三个表的 end_date 是一致的，通常通过 report_type='1' (合并报表) 过滤。
    """
    # 按照报告期倒序查询
    results = (
        db.query(Income, BalanceSheet, CashFlow)
        .join(BalanceSheet, (Income.ts_code == BalanceSheet.ts_code) & (Income.end_date == BalanceSheet.end_date))
        .join(CashFlow, (Income.ts_code == CashFlow.ts_code) & (Income.end_date == CashFlow.end_date))
        .filter(
            Income.ts_code == ts_code,
            # 过滤标准合并报表，通常 '1' 代表合并报表，具体需根据你的数据源定义调整
            Income.report_type == '1', 
            BalanceSheet.report_type == '1',
            CashFlow.report_type == '1'
        )
        .order_by(desc(Income.end_date))
        .limit(limit)
        .all()
    )
    
    # 将结果整理为列表返回，每一项包含三个表的数据对象
    data = []
    for inc, bal, cash in results:
        data.append({
            "end_date": inc.end_date,
            "income": inc,
            "balance": bal,
            "cashflow": cash
        })
    
    # 既然是倒序查出来的，为了计算方便，我们在Service层可能需要正序，这里先保持倒序或按需反转
    return data

def get_comparable_period_data(db: Session, ts_code: str, target_end_date: str):
    """
    获取去年同期的数据，用于计算同比增长率 (YoY)。
    假设 target_end_date 格式为 'YYYYMMDD'
    """
    # 简单的日期处理逻辑：20240331 -> 20230331
    try:
        year = int(target_end_date[:4])
        prev_year_date = f"{year - 1}{target_end_date[4:]}"
    except ValueError:
        return None

    result = (
        db.query(Income)
        .filter(
            Income.ts_code == ts_code,
            Income.end_date == prev_year_date,
            Income.report_type == '1'
        )
        .first()
    )
    return result