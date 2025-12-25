# trend_service.py
from sqlalchemy.orm import Session
from app.crud.crud_trend import get_financial_history,get_comparable_period_data
from typing import List, Dict, Any

def calculate_yoy(current: float, previous: float) -> float:
    """计算同比增长率通用公式"""
    if not previous or previous == 0:
        return 0.0
    # 分母取绝对值，处理去年亏损而今年盈利的情况，保证方向正确
    return ((current - previous) / abs(previous)) * 100

def get_stock_trends(db: Session, ts_code: str) -> Dict[str, Any]:
    """
    接口1逻辑：获取趋势数据（Sparkline数据）
    返回过去8个季度的趋势数组，用于前端画柱状图
    """
    # 获取最近12期数据以确保能算够8期的同比
    history_data = get_financial_history(db, ts_code, limit=12)
    
    # 结果容器
    rev_trends = []        # 收入趋势
    main_profit_trends = [] # 主业利润趋势 (扣非)
    net_profit_trends = []  # 净利润趋势
    prosperity_trends = []  # 景气度趋势
    dates = []

    # 我们遍历最近的数据（history_data是倒序的，即[最新, 次新...]）
    # 为了计算同比，对每一期，我们需要去数据库查它的去年同期
    # 注意：为了性能，实际生产中建议一次性把过去N年数据取出来在内存匹配，这里演示逻辑为主
    
    for item in history_data[:8]: # 只取最近8个季度展示趋势
        curr_inc = item['income']
        curr_date = curr_inc.end_date
        
        # 查去年同期
        prev_inc = crud.get_comparable_period_data(db, ts_code, curr_date)
        
        if not prev_inc:
            # 如果没有同期数据，填0或None
            rev_trends.insert(0, 0)
            main_profit_trends.insert(0, 0)
            net_profit_trends.insert(0, 0)
            prosperity_trends.insert(0, 0)
            dates.insert(0, curr_date)
            continue

        # 1. 收入趋势 (营业收入)
        rev_growth = calculate_yoy(curr_inc.total_revenue, prev_inc.total_revenue)
        
        # 2. 主业利润趋势 (扣除非经常性损益后的净利润)
        # 注意：models.py 中 net_after_nr_lp_correct 是扣非净利
        main_profit_growth = calculate_yoy(curr_inc.net_after_nr_lp_correct, prev_inc.net_after_nr_lp_correct)
        
        # 3. 净利润趋势 (归母净利润)
        net_profit_growth = calculate_yoy(curr_inc.n_income_attr_p, prev_inc.n_income_attr_p)
        
        # 4. 景气度趋势 (自定义复合指标)
        # 简单算法：营收增速和主业利润增速的加权平均
        # 进阶算法可以判断是否“加速”（即本期增速 > 上期增速）
        prosperity_score = (rev_growth * 0.4) + (main_profit_growth * 0.6)
        
        # 插入列表头部（因为要按时间正序返回给前端画图）
        rev_trends.insert(0, round(rev_growth, 2))
        main_profit_trends.insert(0, round(main_profit_growth, 2))
        net_profit_trends.insert(0, round(net_profit_growth, 2))
        prosperity_trends.insert(0, round(prosperity_score, 2))
        dates.insert(0, curr_date)

    return {
        "ts_code": ts_code,
        "dates": dates,
        "revenue_trend": rev_trends,
        "main_profit_trend": main_profit_trends,
        "net_profit_trend": net_profit_trends,
        "prosperity_trend": prosperity_trends
    }

def get_detailed_indicators(db: Session, ts_code: str) -> Dict[str, Any]:
    """
    接口2逻辑：获取单只股票的详细财务指标（截图2内容）
    只取最新一期报告进行计算
    """
    # 获取最新一期
    latest_data_list = get_financial_history(db, ts_code, limit=1)
    if not latest_data_list:
        return {}
    
    data = latest_data_list[0]
    inc = data['income']
    bal = data['balance']
    cash = data['cashflow']
    
    # 获取去年同期用于计算同比增长
    prev_inc = get_comparable_period_data(db, ts_code, inc.end_date)
    # 获取去年同期资产负债表用于计算资产增长（如果需要精确，也需类似逻辑）
    
    # --- 计算逻辑 ---
    
    # 1. 资产合计 & 同比
    total_assets = bal.total_assets
    # 假设 prev_bal 逻辑类似 prev_inc，这里简化省略，设 asset_growth 为示例
    asset_growth = 0.0 # 需补充获取 prev_bal 逻辑
    
    # 2. 资产负债率 = 总负债 / 总资产
    debt_ratio = (bal.total_liab / bal.total_assets * 100) if bal.total_assets else 0
    
    # 3. 股东权益 (归属于母公司股东权益)
    equity = bal.total_hldr_eqy_exc_min_int
    
    # 4. 营业收入 & 同比
    revenue = inc.total_revenue
    rev_growth = calculate_yoy(revenue, prev_inc.total_revenue) if prev_inc else 0
    
    # 5. 毛利率 = (营收 - 成本) / 营收
    # total_cogs 通常包含成本+税金等，如果有单独 oper_cost (营业成本) 更好
    gross_margin = 0
    if inc.total_revenue and inc.oper_cost:
        gross_margin = (inc.total_revenue - inc.oper_cost) / inc.total_revenue * 100
        
    # 6. 费用率 = (销售 + 管理 + 研发 + 财务) / 营收
    # 注意：models.py 中可能有 sell_exp, admin_exp, fin_exp, rd_exp
    expenses = (inc.sell_exp or 0) + (inc.admin_exp or 0) + (inc.fin_exp or 0) + (inc.rd_exp or 0)
    expense_ratio = (expenses / inc.total_revenue * 100) if inc.total_revenue else 0
    
    # 7. 主营利润率 (通常指 扣非净利 / 营收)
    main_profit_ratio = (inc.net_after_nr_lp_correct / inc.total_revenue * 100) if inc.total_revenue else 0
    
    # 8. 净利率 = 净利润 / 营收
    net_margin = (inc.n_income / inc.total_revenue * 100) if inc.total_revenue else 0
    
    # 9. ROE (摊薄) = 归母净利润 / 归母权益
    roe = (inc.n_income_attr_p / bal.total_hldr_eqy_exc_min_int * 100) if bal.total_hldr_eqy_exc_min_int else 0
    
    # 10. 每股收益
    eps = inc.basic_eps
    
    # 11. 现金流
    ocf = cash.n_cashflow_act # 经营现金流
    icf = cash.n_cashflow_inv_act # 投资现金流
    fcf = cash.n_cash_flows_fnc_act # 筹资现金流
    net_cash_inc = cash.n_incr_cash_cash_equ # 现金净增加额

    return {
        "report_date": inc.end_date,
        "total_assets": total_assets,           # 资产合计
        "asset_growth": asset_growth,           # 资产同比
        "debt_asset_ratio": round(debt_ratio, 2), # 资产负债率
        "equity": equity,                       # 股东权益
        "revenue": revenue,                     # 营业收入
        "revenue_growth": round(rev_growth, 2), # 营收同比
        "gross_margin": round(gross_margin, 2), # 毛利率
        "expense_ratio": round(expense_ratio, 2),# 费用率
        "main_profit_ratio": round(main_profit_ratio, 2), # 主营利润率
        "net_margin": round(net_margin, 2),     # 净利率
        "net_profit": inc.n_income_attr_p,      # 净利润(归母)
        "roe": round(roe, 2),                   # ROE
        "eps": eps,                             # EPS
        "ocf": ocf,                             # 经营现金流
        "icf": icf,                             # 投资现金流
        "fcf": fcf,                             # 筹资现金流
        "net_cash_increase": net_cash_inc       # 现金净增加
    }