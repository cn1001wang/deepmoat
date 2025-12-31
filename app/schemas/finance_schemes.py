from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class FinanceSyncLogRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    table_name: str = Field(..., alias="tableName")
    last_sync_end_date: Optional[str] = Field(None, alias="lastSyncEndDate")

class IncomeRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    ann_date: Optional[str] = Field(None, alias="annDate")
    f_ann_date: Optional[str] = Field(None, alias="fAnnDate")
    comp_type: Optional[str] = Field(None, alias="compType")
    end_type: Optional[str] = Field(None, alias="endType")
    basic_eps: Optional[float] = Field(None, alias="basicEps")
    diluted_eps: Optional[float] = Field(None, alias="dilutedEps")
    total_revenue: Optional[float] = Field(None, alias="totalRevenue")
    revenue: Optional[float] = None
    operate_profit: Optional[float] = Field(None, alias="operateProfit")
    total_profit: Optional[float] = Field(None, alias="totalProfit")
    n_income: Optional[float] = Field(None, alias="nIncome")
    n_income_attr_p: Optional[float] = Field(None, alias="nIncomeAttrP")
    rd_exp: Optional[float] = Field(None, alias="rdExp")
    # ... (篇幅原因省略中间类似字段，你可以根据 models.py 补全所有 Float 字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")

class BalanceSheetRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    total_share: Optional[float] = Field(None, alias="totalShare")
    money_cap: Optional[float] = Field(None, alias="moneyCap")
    total_assets: Optional[float] = Field(None, alias="totalAssets")
    total_liab: Optional[float] = Field(None, alias="totalLiab")
    total_hldr_eqy_exc_min_int: Optional[float] = Field(None, alias="totalHldrEqyExcMinInt")
    # ... (根据 models.py 补全所有字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")

class CashFlowRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    net_profit: Optional[float] = Field(None, alias="netProfit")
    n_cashflow_act: Optional[float] = Field(None, alias="nCashflowAct")
    n_cashflow_inv_act: Optional[float] = Field(None, alias="nCashflowInvAct")
    n_cash_flows_fnc_act: Optional[float] = Field(None, alias="nCashFlowsFncAct")
    free_cashflow: Optional[float] = Field(None, alias="freeCashflow")
    # ... (根据 models.py 补全所有字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")


class FinaIndicatorRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")  # TS代码
    ann_date: str = Field(..., alias="annDate")  # 公告日期
    end_date: str = Field(..., alias="endDate")  # 报告期
    eps: Optional[float] = None  # 基本每股收益
    dt_eps: Optional[float] = Field(None, alias="dtEps")  # 稀释每股收益
    total_revenue_ps: Optional[float] = Field(None, alias="totalRevenuePs")  # 每股营业总收入
    revenue_ps: Optional[float] = Field(None, alias="revenuePs")  # 每股营业收入
    capital_rese_ps: Optional[float] = Field(None, alias="capitalResePs")  # 每股资本公积
    surplus_rese_ps: Optional[float] = Field(None, alias="surplusResePs")  # 每股盈余公积
    undist_profit_ps: Optional[float] = Field(None, alias="undistProfitPs")  # 每股未分配利润
    extra_item: Optional[float] = Field(None, alias="extraItem")  # 非经常性损益
    profit_dedt: Optional[float] = Field(None, alias="profitDedt")  # 扣除非经常性损益后的净利润（扣非净利润）
    gross_margin: Optional[float] = Field(None, alias="grossMargin")  # 毛利
    current_ratio: Optional[float] = Field(None, alias="currentRatio")  # 流动比率
    quick_ratio: Optional[float] = Field(None, alias="quickRatio")  # 速动比率
    cash_ratio: Optional[float] = Field(None, alias="cashRatio")  # 保守速动比率
    invturn_days: Optional[float] = Field(None, alias="invturnDays")  # 存货周转天数
    arturn_days: Optional[float] = Field(None, alias="arturnDays")  # 应收账款周转天数
    inv_turn: Optional[float] = Field(None, alias="invTurn")  # 存货周转率
    ar_turn: Optional[float] = Field(None, alias="arTurn")  # 应收账款周转率
    ca_turn: Optional[float] = Field(None, alias="caTurn")  # 流动资产周转率
    fa_turn: Optional[float] = Field(None, alias="faTurn")  # 固定资产周转率
    assets_turn: Optional[float] = Field(None, alias="assetsTurn")  # 总资产周转率
    op_income: Optional[float] = Field(None, alias="opIncome")  # 经营活动净收益
    valuechange_income: Optional[float] = Field(None, alias="valuechangeIncome")  # 价值变动净收益
    interst_income: Optional[float] = Field(None, alias="interstIncome")  # 利息费用
    daa: Optional[float] = None  # 折旧与摊销
    ebit: Optional[float] = None  # 息税前利润
    ebitda: Optional[float] = None  # 息税折旧摊销前利润
    fcff: Optional[float] = None  # 企业自由现金流量
    fcfe: Optional[float] = None  # 股权自由现金流量
    current_exint: Optional[float] = Field(None, alias="currentExint")  # 无息流动负债
    noncurrent_exint: Optional[float] = Field(None, alias="noncurrentExint")  # 无息非流动负债
    interestdebt: Optional[float] = None  # 带息债务
    netdebt: Optional[float] = None  # 净债务
    tangible_asset: Optional[float] = Field(None, alias="tangibleAsset")  # 有形资产
    working_capital: Optional[float] = Field(None, alias="workingCapital")  # 营运资金
    networking_capital: Optional[float] = Field(None, alias="networkingCapital")  # 营运流动资本
    invest_capital: Optional[float] = Field(None, alias="investCapital")  # 全部投入资本
    retained_earnings: Optional[float] = Field(None, alias="retainedEarnings")  # 留存收益
    diluted2_eps: Optional[float] = Field(None, alias="diluted2Eps")  # 期末摊薄每股收益
    bps: Optional[float] = None  # 每股净资产
    ocfps: Optional[float] = None  # 每股经营活动产生的现金流量净额
    retainedps: Optional[float] = None  # 每股留存收益
    cfps: Optional[float] = None  # 每股现金流量净额
    ebit_ps: Optional[float] = Field(None, alias="ebitPs")  # 每股息税前利润
    fcff_ps: Optional[float] = Field(None, alias="fcffPs")  # 每股企业自由现金流量
    fcfe_ps: Optional[float] = Field(None, alias="fcfePs")  # 每股股东自由现金流量
    netprofit_margin: Optional[float] = Field(None, alias="netprofitMargin")  # 销售净利率
    grossprofit_margin: Optional[float] = Field(None, alias="grossprofitMargin")  # 销售毛利率
    cogs_of_sales: Optional[float] = Field(None, alias="cogsOfSales")  # 销售成本率
    expense_of_sales: Optional[float] = Field(None, alias="expenseOfSales")  # 销售期间费用率
    profit_to_gr: Optional[float] = Field(None, alias="profitToGr")  # 净利润/营业总收入
    saleexp_to_gr: Optional[float] = Field(None, alias="saleexpToGr")  # 销售费用/营业总收入
    adminexp_of_gr: Optional[float] = Field(None, alias="adminexpOfGr")  # 管理费用/营业总收入
    finaexp_of_gr: Optional[float] = Field(None, alias="finaexpOfGr")  # 财务费用/营业总收入
    impai_ttm: Optional[float] = Field(None, alias="impaiTtm")  # 资产减值损失/营业总收入
    gc_of_gr: Optional[float] = Field(None, alias="gcOfGr")  # 营业总成本/营业总收入
    op_of_gr: Optional[float] = Field(None, alias="opOfGr")  # 营业利润/营业总收入
    ebit_of_gr: Optional[float] = Field(None, alias="ebitOfGr")  # 息税前利润/营业总收入
    roe: Optional[float] = None  # 净资产收益率
    roe_waa: Optional[float] = Field(None, alias="roeWaa")  # 加权平均净资产收益率
    roe_dt: Optional[float] = Field(None, alias="roeDt")  # 净资产收益率(扣除非经常损益)
    roa: Optional[float] = None  # 总资产报酬率
    npta: Optional[float] = None  # 总资产净利润
    roic: Optional[float] = None  # 投入资本回报率
    roe_yearly: Optional[float] = Field(None, alias="roeYearly")  # 年化净资产收益率
    roa2_yearly: Optional[float] = Field(None, alias="roa2Yearly")  # 年化总资产报酬率
    roe_avg: Optional[float] = Field(None, alias="roeAvg")  # 平均净资产收益率(增发条件)
    opincome_of_ebt: Optional[float] = Field(None, alias="opincomeOfEbt")  # 经营活动净收益/利润总额
    investincome_of_ebt: Optional[float] = Field(None, alias="investincomeOfEbt")  # 价值变动净收益/利润总额
    n_op_profit_of_ebt: Optional[float] = Field(None, alias="nOpProfitOfEbt")  # 营业外收支净额/利润总额
    tax_to_ebt: Optional[float] = Field(None, alias="taxToEbt")  # 所得税/利润总额
    dtprofit_to_profit: Optional[float] = Field(None, alias="dtprofitToProfit")  # 扣除非经常损益后的净利润/净利润
    salescash_to_or: Optional[float] = Field(None, alias="salescashToOr")  # 销售商品提供劳务收到的现金/营业收入
    ocf_to_or: Optional[float] = Field(None, alias="ocfToOr")  # 经营活动产生的现金流量净额/营业收入
    ocf_to_opincome: Optional[float] = Field(None, alias="ocfToOpincome")  # 经营活动产生的现金流量净额/经营活动净收益
    capitalized_to_da: Optional[float] = Field(None, alias="capitalizedToDa")  # 资本支出/折旧和摊销
    debt_to_assets: Optional[float] = Field(None, alias="debtToAssets")  # 资产负债率
    assets_to_eqt: Optional[float] = Field(None, alias="assetsToEqt")  # 权益乘数
    dp_assets_to_eqt: Optional[float] = Field(None, alias="dpAssetsToEqt")  # 权益乘数(杜邦分析)
    ca_to_assets: Optional[float] = Field(None, alias="caToAssets")  # 流动资产/总资产
    nca_to_assets: Optional[float] = Field(None, alias="ncaToAssets")  # 非流动资产/总资产
    tbassets_to_totalassets: Optional[float] = Field(None, alias="tbassetsToTotalassets")  # 有形资产/总资产
    int_to_talcap: Optional[float] = Field(None, alias="intToTalcap")  # 带息债务/全部投入资本
    eqt_to_talcapital: Optional[float] = Field(None, alias="eqtToTalcapital")  # 归属于母公司的股东权益/全部投入资本
    currentdebt_to_debt: Optional[float] = Field(None, alias="currentdebtToDebt")  # 流动负债/负债合计
    longdeb_to_debt: Optional[float] = Field(None, alias="longdebToDebt")  # 非流动负债/负债合计
    ocf_to_shortdebt: Optional[float] = Field(None, alias="ocfToShortdebt")  # 经营活动产生的现金流量净额/流动负债
    debt_to_eqt: Optional[float] = Field(None, alias="debtToEqt")  # 产权比率
    eqt_to_debt: Optional[float] = Field(None, alias="eqtToDebt")  # 归属于母公司的股东权益/负债合计
    eqt_to_interestdebt: Optional[float] = Field(None, alias="eqtToInterestdebt")  # 归属于母公司的股东权益/带息债务
    tangibleasset_to_debt: Optional[float] = Field(None, alias="tangibleassetToDebt")  # 有形资产/负债合计
    tangasset_to_intdebt: Optional[float] = Field(None, alias="tangassetToIntdebt")  # 有形资产/带息债务
    tangibleasset_to_netdebt: Optional[float] = Field(None, alias="tangibleassetToNetdebt")  # 有形资产/净债务
    ocf_to_debt: Optional[float] = Field(None, alias="ocfToDebt")  # 经营活动产生的现金流量净额/负债合计
    ocf_to_interestdebt: Optional[float] = Field(None, alias="ocfToInterestdebt")  # 经营活动产生的现金流量净额/带息债务
    ocf_to_netdebt: Optional[float] = Field(None, alias="ocfToNetdebt")  # 经营活动产生的现金流量净额/净债务
    ebit_to_interest: Optional[float] = Field(None, alias="ebitToInterest")  # 已获利息倍数(EBIT/利息费用)
    longdebt_to_workingcapital: Optional[float] = Field(None, alias="longdebtToWorkingcapital")  # 长期债务与营运资金比率
    ebitda_to_debt: Optional[float] = Field(None, alias="ebitdaToDebt")  # 息税折旧摊销前利润/负债合计
    turn_days: Optional[float] = Field(None, alias="turnDays")  # 营业周期
    roa_yearly: Optional[float] = Field(None, alias="roaYearly")  # 年化总资产净利率
    roa_dp: Optional[float] = Field(None, alias="roaDp")  # 总资产净利率(杜邦分析)
    fixed_assets: Optional[float] = Field(None, alias="fixedAssets")  # 固定资产合计
    profit_prefin_exp: Optional[float] = Field(None, alias="profitPrefinExp")  # 扣除财务费用前营业利润
    non_op_profit: Optional[float] = Field(None, alias="nonOpProfit")  # 非营业利润
    op_to_ebt: Optional[float] = Field(None, alias="opToEbt")  # 营业利润／利润总额
    nop_to_ebt: Optional[float] = Field(None, alias="nopToEbt")  # 非营业利润／利润总额
    ocf_to_profit: Optional[float] = Field(None, alias="ocfToProfit")  # 经营活动产生的现金流量净额／营业利润
    cash_to_liqdebt: Optional[float] = Field(None, alias="cashToLiqdebt")  # 货币资金／流动负债
    cash_to_liqdebt_withinterest: Optional[float] = Field(None, alias="cashToLiqdebtWithinterest")  # 货币资金／带息流动负债
    op_to_liqdebt: Optional[float] = Field(None, alias="opToLiqdebt")  # 营业利润／流动负债
    op_to_debt: Optional[float] = Field(None, alias="opToDebt")  # 营业利润／负债合计
    roic_yearly: Optional[float] = Field(None, alias="roicYearly")  # 年化投入资本回报率
    total_fa_trun: Optional[float] = Field(None, alias="totalFaTrun")  # 固定资产合计周转率
    profit_to_op: Optional[float] = Field(None, alias="profitToOp")  # 利润总额／营业收入
    q_opincome: Optional[float] = Field(None, alias="qOpincome")  # 经营活动单季度净收益
    q_investincome: Optional[float] = Field(None, alias="qInvestincome")  # 价值变动单季度净收益
    q_dtprofit: Optional[float] = Field(None, alias="qDtprofit")  # 扣除非经常损益后的单季度净利润
    q_eps: Optional[float] = Field(None, alias="qEps")  # 每股收益(单季度)
    q_netprofit_margin: Optional[float] = Field(None, alias="qNetprofitMargin")  # 销售净利率(单季度)
    q_gsprofit_margin: Optional[float] = Field(None, alias="qGsprofitMargin")  # 销售毛利率(单季度)
    q_exp_to_sales: Optional[float] = Field(None, alias="qExpToSales")  # 销售期间费用率(单季度)
    q_profit_to_gr: Optional[float] = Field(None, alias="qProfitToGr")  # 净利润／营业总收入(单季度)
    q_saleexp_to_gr: Optional[float] = Field(None, alias="qSaleexpToGr")  # 销售费用／营业总收入 (单季度)
    q_adminexp_to_gr: Optional[float] = Field(None, alias="qAdminexpToGr")  # 管理费用／营业总收入 (单季度)
    q_finaexp_to_gr: Optional[float] = Field(None, alias="qFinaexpToGr")  # 财务费用／营业总收入 (单季度)
    q_impair_to_gr_ttm: Optional[float] = Field(None, alias="qImpairToGrTtm")  # 资产减值损失／营业总收入(单季度)
    q_gc_to_gr: Optional[float] = Field(None, alias="qGcToGr")  # 营业总成本／营业总收入 (单季度)
    q_op_to_gr: Optional[float] = Field(None, alias="qOpToGr")  # 营业利润／营业总收入(单季度)
    q_roe: Optional[float] = Field(None, alias="qRoe")  # 净资产收益率(单季度)
    q_dt_roe: Optional[float] = Field(None, alias="qDtRoe")  # 净资产单季度收益率(扣除非经常损益)
    q_npta: Optional[float] = Field(None, alias="qNpta")  # 总资产净利润(单季度)
    q_opincome_to_ebt: Optional[float] = Field(None, alias="qOpincomeToEbt")  # 经营活动净收益／利润总额(单季度)
    q_investincome_to_ebt: Optional[float] = Field(None, alias="qInvestincomeToEbt")  # 价值变动净收益／利润总额(单季度)
    q_dtprofit_to_profit: Optional[float] = Field(None, alias="qDtprofitToProfit")  # 扣除非经常损益后的净利润／净利润(单季度)
    q_salescash_to_or: Optional[float] = Field(None, alias="qSalescashToOr")  # 销售商品提供劳务收到的现金／营业收入(单季度)
    q_ocf_to_sales: Optional[float] = Field(None, alias="qOcfToSales")  # 经营活动产生的现金流量净额／营业收入(单季度)
    q_ocf_to_or: Optional[float] = Field(None, alias="qOcfToOr")  # 经营活动产生的现金流量净额／经营活动净收益(单季度)
    basic_eps_yoy: Optional[float] = Field(None, alias="basicEpsYoy")  # 基本每股收益同比增长率(%)
    dt_eps_yoy: Optional[float] = Field(None, alias="dtEpsYoy")  # 稀释每股收益同比增长率(%)
    cfps_yoy: Optional[float] = Field(None, alias="cfpsYoy")  # 每股经营活动产生的现金流量净额同比增长率(%)
    op_yoy: Optional[float] = Field(None, alias="opYoy")  # 营业利润同比增长率(%)
    ebt_yoy: Optional[float] = Field(None, alias="ebtYoy")  # 利润总额同比增长率(%)
    netprofit_yoy: Optional[float] = Field(None, alias="netprofitYoy")  # 归属母公司股东的净利润同比增长率(%)
    dt_netprofit_yoy: Optional[float] = Field(None, alias="dtNetprofitYoy")  # 归属母公司股东的净利润-扣除非经常损益同比增长率(%)
    ocf_yoy: Optional[float] = Field(None, alias="ocfYoy")  # 经营活动产生的现金流量净额同比增长率(%)
    roe_yoy: Optional[float] = Field(None, alias="roeYoy")  # 净资产收益率(摊薄)同比增长率(%)
    bps_yoy: Optional[float] = Field(None, alias="bpsYoy")  # 每股净资产相对年初增长率(%)
    assets_yoy: Optional[float] = Field(None, alias="assetsYoy")  # 资产总计相对年初增长率(%)
    eqt_yoy: Optional[float] = Field(None, alias="eqtYoy")  # 归属母公司的股东权益相对年初增长率(%)
    tr_yoy: Optional[float] = Field(None, alias="trYoy")  # 营业总收入同比增长率(%)
    or_yoy: Optional[float] = Field(None, alias="orYoy")  # 营业收入同比增长率(%)
    q_gr_yoy: Optional[float] = Field(None, alias="qGrYoy")  # 营业总收入同比增长率(%)(单季度)
    q_gr_qoq: Optional[float] = Field(None, alias="qGrQoq")  # 营业总收入环比增长率(%)(单季度)
    q_sales_yoy: Optional[float] = Field(None, alias="qSalesYoy")  # 营业收入同比增长率(%)(单季度)
    q_sales_qoq: Optional[float] = Field(None, alias="qSalesQoq")  # 营业收入环比增长率(%)(单季度)
    q_op_yoy: Optional[float] = Field(None, alias="qOpYoy")  # 营业利润同比增长率(%)(单季度)
    q_op_qoq: Optional[float] = Field(None, alias="qOpQoq")  # 营业利润环比增长率(%)(单季度)
    q_profit_yoy: Optional[float] = Field(None, alias="qProfitYoy")  # 净利润同比增长率(%)(单季度)
    q_profit_qoq: Optional[float] = Field(None, alias="qProfitQoq")  # 净利润环比增长率(%)(单季度)
    q_netprofit_yoy: Optional[float] = Field(None, alias="qNetprofitYoy")  # 归属母公司股东的净利润同比增长率(%)(单季度)
    q_netprofit_qoq: Optional[float] = Field(None, alias="qNetprofitQoq")  # 归属母公司股东的净利润环比增长率(%)(单季度)
    equity_yoy: Optional[float] = Field(None, alias="equityYoy")  # 净资产同比增长率
    rd_exp: Optional[float] = Field(None, alias="rdExp")  # 研发费用
    update_flag: Optional[str] = Field(None, alias="updateFlag")  # 更新标识

class FinaMainbzRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")  # TS代码
    end_date: str = Field(..., alias="endDate")  # 报告期
    bz_item: Optional[str] = Field(None, alias="bzItem")  # 主营业务来源
    bz_sales: Optional[float] = Field(None, alias="bzSales")  # 主营业务收入(元)
    bz_profit: Optional[float] = Field(None, alias="bzProfit")  # 主营业务利润(元)
    bz_cost: Optional[float] = Field(None, alias="bzCost")  # 主营业务成本(元)
    curr_type: Optional[str] = Field(None, alias="currType")  # 货币代码
    update_flag: Optional[str] = Field(None, alias="updateFlag")  # 是否更新
