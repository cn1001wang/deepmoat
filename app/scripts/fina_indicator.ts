export interface FinaIndicator {
  /** TS代码 */
  tsCode: string
  /** 公告日期 */
  annDate: string
  /** 报告期 */
  endDate: string
  /** 基本每股收益 */
  eps?: number
  /** 稀释每股收益 */
  dtEps?: number
  /** 每股营业总收入 */
  totalRevenuePs?: number
  /** 每股营业收入 */
  revenuePs?: number
  /** 每股资本公积 */
  capitalResePs?: number
  /** 每股盈余公积 */
  surplusResePs?: number
  /** 每股未分配利润 */
  undistProfitPs?: number
  /** 非经常性损益 */
  extraItem?: number
  /** 扣除非经常性损益后的净利润（扣非净利润） */
  profitDedt?: number
  /** 毛利 */
  grossMargin?: number
  /** 流动比率 */
  currentRatio?: number
  /** 速动比率 */
  quickRatio?: number
  /** 保守速动比率 */
  cashRatio?: number
  /** 存货周转天数 */
  invturnDays?: number
  /** 应收账款周转天数 */
  arturnDays?: number
  /** 存货周转率 */
  invTurn?: number
  /** 应收账款周转率 */
  arTurn?: number
  /** 流动资产周转率 */
  caTurn?: number
  /** 固定资产周转率 */
  faTurn?: number
  /** 总资产周转率 */
  assetsTurn?: number
  /** 经营活动净收益 */
  opIncome?: number
  /** 价值变动净收益 */
  valuechangeIncome?: number
  /** 利息费用 */
  interstIncome?: number
  /** 折旧与摊销 */
  daa?: number
  /** 息税前利润 */
  ebit?: number
  /** 息税折旧摊销前利润 */
  ebitda?: number
  /** 企业自由现金流量 */
  fcff?: number
  /** 股权自由现金流量 */
  fcfe?: number
  /** 无息流动负债 */
  currentExint?: number
  /** 无息非流动负债 */
  noncurrentExint?: number
  /** 带息债务 */
  interestdebt?: number
  /** 净债务 */
  netdebt?: number
  /** 有形资产 */
  tangibleAsset?: number
  /** 营运资金 */
  workingCapital?: number
  /** 营运流动资本 */
  networkingCapital?: number
  /** 全部投入资本 */
  investCapital?: number
  /** 留存收益 */
  retainedEarnings?: number
  /** 期末摊薄每股收益 */
  diluted2Eps?: number
  /** 每股净资产 */
  bps?: number
  /** 每股经营活动产生的现金流量净额 */
  ocfps?: number
  /** 每股留存收益 */
  retainedps?: number
  /** 每股现金流量净额 */
  cfps?: number
  /** 每股息税前利润 */
  ebitPs?: number
  /** 每股企业自由现金流量 */
  fcffPs?: number
  /** 每股股东自由现金流量 */
  fcfePs?: number
  /** 销售净利率 */
  netprofitMargin?: number
  /** 销售毛利率 */
  grossprofitMargin?: number
  /** 销售成本率 */
  cogsOfSales?: number
  /** 销售期间费用率 */
  expenseOfSales?: number
  /** 净利润/营业总收入 */
  profitToGr?: number
  /** 销售费用/营业总收入 */
  saleexpToGr?: number
  /** 管理费用/营业总收入 */
  adminexpOfGr?: number
  /** 财务费用/营业总收入 */
  finaexpOfGr?: number
  /** 资产减值损失/营业总收入 */
  impaiTtm?: number
  /** 营业总成本/营业总收入 */
  gcOfGr?: number
  /** 营业利润/营业总收入 */
  opOfGr?: number
  /** 息税前利润/营业总收入 */
  ebitOfGr?: number
  /** 净资产收益率 */
  roe?: number
  /** 加权平均净资产收益率 */
  roeWaa?: number
  /** 净资产收益率(扣除非经常损益) */
  roeDt?: number
  /** 总资产报酬率 */
  roa?: number
  /** 总资产净利润 */
  npta?: number
  /** 投入资本回报率 */
  roic?: number
  /** 年化净资产收益率 */
  roeYearly?: number
  /** 年化总资产报酬率 */
  roa2Yearly?: number
  /** 平均净资产收益率(增发条件) */
  roeAvg?: number
  /** 经营活动净收益/利润总额 */
  opincomeOfEbt?: number
  /** 价值变动净收益/利润总额 */
  investincomeOfEbt?: number
  /** 营业外收支净额/利润总额 */
  nOpProfitOfEbt?: number
  /** 所得税/利润总额 */
  taxToEbt?: number
  /** 扣除非经常损益后的净利润/净利润 */
  dtprofitToProfit?: number
  /** 销售商品提供劳务收到的现金/营业收入 */
  salescashToOr?: number
  /** 经营活动产生的现金流量净额/营业收入 */
  ocfToOr?: number
  /** 经营活动产生的现金流量净额/经营活动净收益 */
  ocfToOpincome?: number
  /** 资本支出/折旧和摊销 */
  capitalizedToDa?: number
  /** 资产负债率 */
  debtToAssets?: number
  /** 权益乘数 */
  assetsToEqt?: number
  /** 权益乘数(杜邦分析) */
  dpAssetsToEqt?: number
  /** 流动资产/总资产 */
  caToAssets?: number
  /** 非流动资产/总资产 */
  ncaToAssets?: number
  /** 有形资产/总资产 */
  tbassetsToTotalassets?: number
  /** 带息债务/全部投入资本 */
  intToTalcap?: number
  /** 归属于母公司的股东权益/全部投入资本 */
  eqtToTalcapital?: number
  /** 流动负债/负债合计 */
  currentdebtToDebt?: number
  /** 非流动负债/负债合计 */
  longdebToDebt?: number
  /** 经营活动产生的现金流量净额/流动负债 */
  ocfToShortdebt?: number
  /** 产权比率 */
  debtToEqt?: number
  /** 归属于母公司的股东权益/负债合计 */
  eqtToDebt?: number
  /** 归属于母公司的股东权益/带息债务 */
  eqtToInterestdebt?: number
  /** 有形资产/负债合计 */
  tangibleassetToDebt?: number
  /** 有形资产/带息债务 */
  tangassetToIntdebt?: number
  /** 有形资产/净债务 */
  tangibleassetToNetdebt?: number
  /** 经营活动产生的现金流量净额/负债合计 */
  ocfToDebt?: number
  /** 经营活动产生的现金流量净额/带息债务 */
  ocfToInterestdebt?: number
  /** 经营活动产生的现金流量净额/净债务 */
  ocfToNetdebt?: number
  /** 已获利息倍数(EBIT/利息费用) */
  ebitToInterest?: number
  /** 长期债务与营运资金比率 */
  longdebtToWorkingcapital?: number
  /** 息税折旧摊销前利润/负债合计 */
  ebitdaToDebt?: number
  /** 营业周期 */
  turnDays?: number
  /** 年化总资产净利率 */
  roaYearly?: number
  /** 总资产净利率(杜邦分析) */
  roaDp?: number
  /** 固定资产合计 */
  fixedAssets?: number
  /** 扣除财务费用前营业利润 */
  profitPrefinExp?: number
  /** 非营业利润 */
  nonOpProfit?: number
  /** 营业利润／利润总额 */
  opToEbt?: number
  /** 非营业利润／利润总额 */
  nopToEbt?: number
  /** 经营活动产生的现金流量净额／营业利润 */
  ocfToProfit?: number
  /** 货币资金／流动负债 */
  cashToLiqdebt?: number
  /** 货币资金／带息流动负债 */
  cashToLiqdebtWithinterest?: number
  /** 营业利润／流动负债 */
  opToLiqdebt?: number
  /** 营业利润／负债合计 */
  opToDebt?: number
  /** 年化投入资本回报率 */
  roicYearly?: number
  /** 固定资产合计周转率 */
  totalFaTrun?: number
  /** 利润总额／营业收入 */
  profitToOp?: number
  /** 经营活动单季度净收益 */
  qOpincome?: number
  /** 价值变动单季度净收益 */
  qInvestincome?: number
  /** 扣除非经常损益后的单季度净利润 */
  qDtprofit?: number
  /** 每股收益(单季度) */
  qEps?: number
  /** 销售净利率(单季度) */
  qNetprofitMargin?: number
  /** 销售毛利率(单季度) */
  qGsprofitMargin?: number
  /** 销售期间费用率(单季度) */
  qExpToSales?: number
  /** 净利润／营业总收入(单季度) */
  qProfitToGr?: number
  /** 销售费用／营业总收入 (单季度) */
  qSaleexpToGr?: number
  /** 管理费用／营业总收入 (单季度) */
  qAdminexpToGr?: number
  /** 财务费用／营业总收入 (单季度) */
  qFinaexpToGr?: number
  /** 资产减值损失／营业总收入(单季度) */
  qImpairToGrTtm?: number
  /** 营业总成本／营业总收入 (单季度) */
  qGcToGr?: number
  /** 营业利润／营业总收入(单季度) */
  qOpToGr?: number
  /** 净资产收益率(单季度) */
  qRoe?: number
  /** 净资产单季度收益率(扣除非经常损益) */
  qDtRoe?: number
  /** 总资产净利润(单季度) */
  qNpta?: number
  /** 经营活动净收益／利润总额(单季度) */
  qOpincomeToEbt?: number
  /** 价值变动净收益／利润总额(单季度) */
  qInvestincomeToEbt?: number
  /** 扣除非经常损益后的净利润／净利润(单季度) */
  qDtprofitToProfit?: number
  /** 销售商品提供劳务收到的现金／营业收入(单季度) */
  qSalescashToOr?: number
  /** 经营活动产生的现金流量净额／营业收入(单季度) */
  qOcfToSales?: number
  /** 经营活动产生的现金流量净额／经营活动净收益(单季度) */
  qOcfToOr?: number
  /** 基本每股收益同比增长率(%) */
  basicEpsYoy?: number
  /** 稀释每股收益同比增长率(%) */
  dtEpsYoy?: number
  /** 每股经营活动产生的现金流量净额同比增长率(%) */
  cfpsYoy?: number
  /** 营业利润同比增长率(%) */
  opYoy?: number
  /** 利润总额同比增长率(%) */
  ebtYoy?: number
  /** 归属母公司股东的净利润同比增长率(%) */
  netprofitYoy?: number
  /** 归属母公司股东的净利润-扣除非经常损益同比增长率(%) */
  dtNetprofitYoy?: number
  /** 经营活动产生的现金流量净额同比增长率(%) */
  ocfYoy?: number
  /** 净资产收益率(摊薄)同比增长率(%) */
  roeYoy?: number
  /** 每股净资产相对年初增长率(%) */
  bpsYoy?: number
  /** 资产总计相对年初增长率(%) */
  assetsYoy?: number
  /** 归属母公司的股东权益相对年初增长率(%) */
  eqtYoy?: number
  /** 营业总收入同比增长率(%) */
  trYoy?: number
  /** 营业收入同比增长率(%) */
  orYoy?: number
  /** 营业总收入同比增长率(%)(单季度) */
  qGrYoy?: number
  /** 营业总收入环比增长率(%)(单季度) */
  qGrQoq?: number
  /** 营业收入同比增长率(%)(单季度) */
  qSalesYoy?: number
  /** 营业收入环比增长率(%)(单季度) */
  qSalesQoq?: number
  /** 营业利润同比增长率(%)(单季度) */
  qOpYoy?: number
  /** 营业利润环比增长率(%)(单季度) */
  qOpQoq?: number
  /** 净利润同比增长率(%)(单季度) */
  qProfitYoy?: number
  /** 净利润环比增长率(%)(单季度) */
  qProfitQoq?: number
  /** 归属母公司股东的净利润同比增长率(%)(单季度) */
  qNetprofitYoy?: number
  /** 归属母公司股东的净利润环比增长率(%)(单季度) */
  qNetprofitQoq?: number
  /** 净资产同比增长率 */
  equityYoy?: number
  /** 研发费用 */
  rdExp?: number
  /** 更新标识 */
  updateFlag?: string
}
