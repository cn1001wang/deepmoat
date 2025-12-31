from sqlalchemy import Column, String, Float, Integer
from app.db.session import Base

class SwIndustry(Base):
    __tablename__ = "sw_industry"

    index_code = Column(String(20), primary_key=True, index=True)
    industry_name = Column(String(100))
    parent_code = Column(String(20))
    level = Column(String(10))
    industry_code = Column(String(20))
    is_pub = Column(String(5))
    src = Column(String(20))
    def to_dict(self):
        return {
            "indexCode": self.index_code,
            "industryName": self.industry_name,
            "parentCode": self.parent_code,
            "level": self.level,
            "industryCode": self.industry_code,
            "isPub": self.is_pub,
            "src": self.src,
        }
class IndexMember(Base):
    __tablename__ = "index_member"

    l1_code = Column(String(20), primary_key=True)
    l1_name = Column(String(100))
    l2_code = Column(String(20))
    l2_name = Column(String(100))
    l3_code = Column(String(20))
    l3_name = Column(String(100))
    ts_code = Column(String(20), primary_key=True)
    name = Column(String(100))
    in_date = Column(String(20))
    out_date = Column(String(20))
    is_new = Column(String(5))

    def to_dict(self):
        return {
            "l1Code": self.l1_code,
            "l1Name": self.l1_name,
            "l2Code": self.l2_code,
            "l2Name": self.l2_name,
            "l3Code": self.l3_code,
            "l3Name": self.l3_name,
            "tsCode": self.ts_code,
            "name": self.name,
            "inDate": self.in_date,
            "outDate": self.out_date,
            "isNew": self.is_new,
        }

class StockBasic(Base):
    __tablename__ = "stock_basic"

    ts_code = Column(String(20), primary_key=True, index=True)

    symbol = Column(String(20))
    name = Column(String(50))
    fullname = Column(String(100))
    ennname = Column(String(100))
    cnspell = Column(String(50))

    area = Column(String(50))
    industry = Column(String(50))

    market = Column(String(20))
    exchange = Column(String(20))
    curr_type = Column(String(10))
    list_status = Column(String(10))

    list_date = Column(String(20))
    delist_date = Column(String(20))

    is_hs = Column(String(5))
    act_name = Column(String(100))
    act_ent_type = Column(String(50))
    def to_dict(self):
        return {
            "tsCode": self.ts_code,
            "symbol": self.symbol,
            "name": self.name,
            "fullname": self.fullname,
            "ennname": self.ennname,
            "cnspell": self.cnspell,
            "area": self.area,
            "industry": self.industry,
            "market": self.market,
            "exchange": self.exchange,
            "currType": self.curr_type,
            "listStatus": self.list_status,
            "listDate": self.list_date,
            "delistDate": self.delist_date,
            "isHs": self.is_hs,
            "actName": self.act_name,
            "actEntType": self.act_ent_type,
        }

# 股票公司信息
class StockCompany(Base):
    __tablename__ = "stock_company"

    ts_code = Column(String(20), primary_key=True, index=True)

    com_name = Column(String(200))
    com_id = Column(String(50))
    exchange = Column(String(20))

    chairman = Column(String(100))
    manager = Column(String(100))
    secretary = Column(String(100))

    reg_capital = Column(Float)
    setup_date = Column(String(20))

    province = Column(String(50))
    city = Column(String(50))
    introduction = Column(String(2000))

    website = Column(String(200))
    email = Column(String(100))
    office = Column(String(100))
    main_business = Column(String(2000))
    business_scope = Column(String(2000))

    employees = Column(Integer)
    def to_dict(self):
        return {
            "tsCode": self.ts_code,
            "comName": self.com_name,
            "comId": self.com_id,
            "exchange": self.exchange,
            "chairman": self.chairman,
            "manager": self.manager,
            "secretary": self.secretary,
            "regCapital": self.reg_capital,
            "setupDate": self.setup_date,
            "province": self.province,
            "city": self.city,
            "website": self.website,
            "email": self.email,
            "employees": self.employees,
        }

class FinanceSyncLog(Base):
    __tablename__ = "finance_sync_log"

    ts_code = Column(String(20), primary_key=True)
    table_name = Column(String(20), primary_key=True)  # income / balancesheet / cashflow
    last_sync_end_date = Column(String(20))  # 最近一次同步到的报告期

# 利润表
class Income(Base):
    __tablename__ = "income"

    ts_code = Column(String(20), primary_key=True)
    end_date = Column(String(20), primary_key=True)
    report_type = Column(String(10), primary_key=True)

    ann_date = Column(String(20))
    f_ann_date = Column(String(20))
    comp_type = Column(String(10))
    end_type = Column(String(10))

    basic_eps = Column(Float)
    diluted_eps = Column(Float)
    total_revenue = Column(Float)
    revenue = Column(Float)
    int_income = Column(Float)
    prem_earned = Column(Float)
    comm_income = Column(Float)
    n_commis_income = Column(Float)
    n_oth_income = Column(Float)
    n_oth_b_income = Column(Float)
    prem_income = Column(Float)
    out_prem = Column(Float)
    une_prem_reser = Column(Float)
    reins_income = Column(Float)
    n_sec_tb_income = Column(Float)
    n_sec_uw_income = Column(Float)
    n_asset_mg_income = Column(Float)
    oth_b_income = Column(Float)
    fv_value_chg_gain = Column(Float)
    invest_income = Column(Float)
    ass_invest_income = Column(Float)
    forex_gain = Column(Float)

    total_cogs = Column(Float)
    oper_cost = Column(Float)
    int_exp = Column(Float)
    comm_exp = Column(Float)
    biz_tax_surchg = Column(Float)
    sell_exp = Column(Float)
    admin_exp = Column(Float)
    fin_exp = Column(Float)
    assets_impair_loss = Column(Float)

    prem_refund = Column(Float)
    compens_payout = Column(Float)
    reser_insur_liab = Column(Float)
    div_payt = Column(Float)
    reins_exp = Column(Float)
    oper_exp = Column(Float)
    compens_payout_refu = Column(Float)
    insur_reser_refu = Column(Float)
    reins_cost_refund = Column(Float)
    other_bus_cost = Column(Float)

    operate_profit = Column(Float)
    non_oper_income = Column(Float)
    non_oper_exp = Column(Float)
    nca_disploss = Column(Float)
    total_profit = Column(Float)
    income_tax = Column(Float)

    n_income = Column(Float)
    n_income_attr_p = Column(Float)
    minority_gain = Column(Float)

    oth_compr_income = Column(Float)
    t_compr_income = Column(Float)
    compr_inc_attr_p = Column(Float)
    compr_inc_attr_m_s = Column(Float)

    ebit = Column(Float)
    ebitda = Column(Float)

    insurance_exp = Column(Float)
    undist_profit = Column(Float)
    distable_profit = Column(Float)
    rd_exp = Column(Float)

    fin_exp_int_exp = Column(Float)
    fin_exp_int_inc = Column(Float)

    transfer_surplus_rese = Column(Float)
    transfer_housing_imprest = Column(Float)
    transfer_oth = Column(Float)
    adj_lossgain = Column(Float)

    withdra_legal_surplus = Column(Float)
    withdra_legal_pubfund = Column(Float)
    withdra_biz_devfund = Column(Float)
    withdra_rese_fund = Column(Float)
    withdra_oth_ersu = Column(Float)

    workers_welfare = Column(Float)
    distr_profit_shrhder = Column(Float)
    prfshare_payable_dvd = Column(Float)
    comshare_payable_dvd = Column(Float)
    capit_comstock_div = Column(Float)

    net_after_nr_lp_correct = Column(Float)
    credit_impa_loss = Column(Float)
    net_expo_hedging_benefits = Column(Float)
    oth_impair_loss_assets = Column(Float)
    total_opcost = Column(Float)
    amodcost_fin_assets = Column(Float)
    oth_income = Column(Float)
    asset_disp_income = Column(Float)
    continued_net_profit = Column(Float)
    end_net_profit = Column(Float)

    update_flag = Column(String(10))

# 资产负债表
class BalanceSheet(Base):
    __tablename__ = "balancesheet"

    ts_code = Column(String(20), primary_key=True)
    end_date = Column(String(20), primary_key=True)
    report_type = Column(String(10), primary_key=True)

    ann_date = Column(String(20))
    f_ann_date = Column(String(20))
    comp_type = Column(String(10))
    end_type = Column(String(10))

    total_share = Column(Float)
    cap_rese = Column(Float)
    undistr_porfit = Column(Float)
    surplus_rese = Column(Float)
    special_rese = Column(Float)

    money_cap = Column(Float)
    trad_asset = Column(Float)
    notes_receiv = Column(Float)
    accounts_receiv = Column(Float)
    oth_receiv = Column(Float)
    prepayment = Column(Float)
    div_receiv = Column(Float)
    int_receiv = Column(Float)
    inventories = Column(Float)
    amor_exp = Column(Float)
    nca_within_1y = Column(Float)

    oth_cur_assets = Column(Float)
    total_cur_assets = Column(Float)

    fa_avail_for_sale = Column(Float)
    htm_invest = Column(Float)
    lt_eqt_invest = Column(Float)
    invest_real_estate = Column(Float)
    time_deposits = Column(Float)
    oth_assets = Column(Float)
    fix_assets = Column(Float)
    cip = Column(Float)
    intan_assets = Column(Float)
    goodwill = Column(Float)
    defer_tax_assets = Column(Float)
    oth_nca = Column(Float)
    total_nca = Column(Float)

    total_assets = Column(Float)

    st_borr = Column(Float)
    lt_borr = Column(Float)
    notes_payable = Column(Float)
    acct_payable = Column(Float)
    adv_receipts = Column(Float)
    taxes_payable = Column(Float)
    oth_payable = Column(Float)

    total_cur_liab = Column(Float)
    bond_payable = Column(Float)
    defer_tax_liab = Column(Float)
    oth_ncl = Column(Float)
    total_ncl = Column(Float)

    total_liab = Column(Float)

    treasury_share = Column(Float)
    minority_int = Column(Float)
    total_hldr_eqy_exc_min_int = Column(Float)
    total_hldr_eqy_inc_min_int = Column(Float)

    total_liab_hldr_eqy = Column(Float)

    update_flag = Column(String(10))

# 现金流量表
class CashFlow(Base):
    __tablename__ = "cashflow"

    ts_code = Column(String(20), primary_key=True)
    end_date = Column(String(20), primary_key=True)
    report_type = Column(String(10), primary_key=True)

    ann_date = Column(String(20))
    f_ann_date = Column(String(20))
    comp_type = Column(String(10))
    end_type = Column(String(10))

    net_profit = Column(Float)
    finan_exp = Column(Float)

    c_fr_sale_sg = Column(Float)
    recp_tax_rends = Column(Float)
    c_inf_fr_operate_a = Column(Float)

    c_paid_goods_s = Column(Float)
    c_paid_to_for_empl = Column(Float)
    c_paid_for_taxes = Column(Float)
    st_cash_out_act = Column(Float)

    n_cashflow_act = Column(Float)

    c_disp_withdrwl_invest = Column(Float)
    c_recp_return_invest = Column(Float)
    stot_inflows_inv_act = Column(Float)

    c_pay_acq_const_fiolta = Column(Float)
    c_paid_invest = Column(Float)
    stot_out_inv_act = Column(Float)

    n_cashflow_inv_act = Column(Float)

    c_recp_borrow = Column(Float)
    proc_issue_bonds = Column(Float)
    stot_cash_in_fnc_act = Column(Float)

    c_prepay_amt_borr = Column(Float)
    c_pay_dist_dpcp_int_exp = Column(Float)
    stot_cashout_fnc_act = Column(Float)

    n_cash_flows_fnc_act = Column(Float)

    free_cashflow = Column(Float)

    eff_fx_flu_cash = Column(Float)
    n_incr_cash_cash_equ = Column(Float)

    c_cash_equ_beg_period = Column(Float)
    c_cash_equ_end_period = Column(Float)

    update_flag = Column(String(10))


class DailyBasic(Base):
    __tablename__ = "daily_basic"

    ts_code = Column(String(20), primary_key=True, comment="TS股票代码")
    trade_date = Column(String(8), primary_key=True, comment="交易日期 YYYYMMDD")

    close = Column(Float, comment="当日收盘价")

    turnover_rate = Column(Float, comment="换手率（%）")
    turnover_rate_f = Column(Float, comment="换手率（自由流通股）")
    volume_ratio = Column(Float, comment="量比")

    pe = Column(Float, comment="市盈率（总市值/净利润，亏损PE为空）")
    pe_ttm = Column(Float, comment="市盈率（TTM，亏损PE为空）")

    pb = Column(Float, comment="市净率（总市值/净资产）")

    ps = Column(Float, comment="市销率")
    ps_ttm = Column(Float, comment="市销率（TTM）")

    dv_ratio = Column(Float, comment="股息率（%）")
    dv_ttm = Column(Float, comment="股息率（TTM）（%）")

    total_share = Column(Float, comment="总股本（万股）")
    float_share = Column(Float, comment="流通股本（万股）")
    free_share = Column(Float, comment="自由流通股本（万股）")

    total_mv = Column(Float, comment="总市值（万元）")
    circ_mv = Column(Float, comment="流通市值（万元）")

from sqlalchemy import (
    Column,
    String,
    Float,
    UniqueConstraint,
)
from app.db.base import Base


class DailyBasic(Base):
    __tablename__ = "daily_basic"
    __table_args__ = (
        UniqueConstraint("ts_code", "ann_date", "end_date", name="uk_daily_basic"),
    )

    ts_code = Column(String(20), nullable=False, comment="TS代码")
    ann_date = Column(String(8), nullable=False, comment="公告日期")
    end_date = Column(String(8), nullable=False, comment="报告期")

    eps = Column(Float, nullable=False, comment="基本每股收益")
    dt_eps = Column(Float, nullable=False, comment="稀释每股收益")
    total_revenue_ps = Column(Float, nullable=False, comment="每股营业总收入")
    revenue_ps = Column(Float, nullable=False, comment="每股营业收入")
    capital_rese_ps = Column(Float, nullable=False, comment="每股资本公积")
    surplus_rese_ps = Column(Float, nullable=False, comment="每股盈余公积")
    undist_profit_ps = Column(Float, nullable=False, comment="每股未分配利润")
    extra_item = Column(Float, nullable=False, comment="非经常性损益")
    profit_dedt = Column(Float, nullable=False, comment="扣非净利润")
    gross_margin = Column(Float, nullable=False, comment="毛利")
    current_ratio = Column(Float, nullable=False, comment="流动比率")
    quick_ratio = Column(Float, nullable=False, comment="速动比率")
    cash_ratio = Column(Float, nullable=False, comment="保守速动比率")

    invturn_days = Column(Float, nullable=True, comment="存货周转天数")
    arturn_days = Column(Float, nullable=True, comment="应收账款周转天数")
    inv_turn = Column(Float, nullable=True, comment="存货周转率")
    ar_turn = Column(Float, nullable=False, comment="应收账款周转率")
    ca_turn = Column(Float, nullable=False, comment="流动资产周转率")
    fa_turn = Column(Float, nullable=False, comment="固定资产周转率")
    assets_turn = Column(Float, nullable=False, comment="总资产周转率")

    op_income = Column(Float, nullable=False, comment="经营活动净收益")
    valuechange_income = Column(Float, nullable=True, comment="价值变动净收益")
    interst_income = Column(Float, nullable=True, comment="利息费用")
    daa = Column(Float, nullable=True, comment="折旧与摊销")

    ebit = Column(Float, nullable=False, comment="息税前利润")
    ebitda = Column(Float, nullable=False, comment="息税折旧摊销前利润")
    fcff = Column(Float, nullable=False, comment="企业自由现金流量")
    fcfe = Column(Float, nullable=False, comment="股权自由现金流量")

    current_exint = Column(Float, nullable=False, comment="无息流动负债")
    noncurrent_exint = Column(Float, nullable=False, comment="无息非流动负债")
    interestdebt = Column(Float, nullable=False, comment="带息债务")
    netdebt = Column(Float, nullable=False, comment="净债务")
    tangible_asset = Column(Float, nullable=False, comment="有形资产")

    working_capital = Column(Float, nullable=False, comment="营运资金")
    networking_capital = Column(Float, nullable=False, comment="营运流动资本")
    invest_capital = Column(Float, nullable=False, comment="全部投入资本")
    retained_earnings = Column(Float, nullable=False, comment="留存收益")

    diluted2_eps = Column(Float, nullable=False, comment="期末摊薄每股收益")
    bps = Column(Float, nullable=False, comment="每股净资产")
    ocfps = Column(Float, nullable=False, comment="每股经营现金流")
    retainedps = Column(Float, nullable=False, comment="每股留存收益")
    cfps = Column(Float, nullable=False, comment="每股现金流量净额")

    ebit_ps = Column(Float, nullable=False, comment="每股息税前利润")
    fcff_ps = Column(Float, nullable=False, comment="每股企业自由现金流")
    fcfe_ps = Column(Float, nullable=False, comment="每股股东自由现金流")

    netprofit_margin = Column(Float, nullable=False, comment="销售净利率")
    grossprofit_margin = Column(Float, nullable=False, comment="销售毛利率")
    cogs_of_sales = Column(Float, nullable=False, comment="销售成本率")
    expense_of_sales = Column(Float, nullable=False, comment="销售期间费用率")
    profit_to_gr = Column(Float, nullable=False, comment="净利润/营业总收入")

    saleexp_to_gr = Column(Float, nullable=False, comment="销售费用/营业总收入")
    adminexp_of_gr = Column(Float, nullable=False, comment="管理费用/营业总收入")
    finaexp_of_gr = Column(Float, nullable=False, comment="财务费用/营业总收入")
    impai_ttm = Column(Float, nullable=False, comment="资产减值损失/营业总收入")
    gc_of_gr = Column(Float, nullable=False, comment="营业总成本/营业总收入")
    op_of_gr = Column(Float, nullable=False, comment="营业利润/营业总收入")
    ebit_of_gr = Column(Float, nullable=False, comment="息税前利润/营业总收入")

    roe = Column(Float, nullable=False, comment="净资产收益率")
    roe_waa = Column(Float, nullable=False, comment="加权ROE")
    roe_dt = Column(Float, nullable=False, comment="扣非ROE")
    roa = Column(Float, nullable=False, comment="总资产报酬率")
    npta = Column(Float, nullable=False, comment="总资产净利润")
    roic = Column(Float, nullable=False, comment="投入资本回报率")

    roe_yearly = Column(Float, nullable=False, comment="年化ROE")
    roa2_yearly = Column(Float, nullable=False, comment="年化ROA")
    roe_avg = Column(Float, nullable=True, comment="平均ROE(增发条件)")

    debt_to_assets = Column(Float, nullable=False, comment="资产负债率")
    assets_to_eqt = Column(Float, nullable=False, comment="权益乘数")
    dp_assets_to_eqt = Column(Float, nullable=False, comment="权益乘数(杜邦)")

    update_flag = Column(String(8), nullable=True, comment="更新标识")
