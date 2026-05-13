<script setup lang="ts">
import type { BarSeriesOption, ECharts, EChartsOption, LineSeriesOption, PieSeriesOption } from 'echarts'
import type { FinanceCardPoint, FinanceCardResponse, MainBusinessPoint, ValuationPoint } from '@/api/finance'
import type { ComponentPublicInstance } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getFinanceCard } from '@/api/finance'

interface ChartSpec {
  id: string
  option: EChartsOption
  className?: string
  fieldRows?: FieldSpec[]
  readingGuide?: string[]
}

interface FieldSpec {
  label: string
  cnFields: string
  fields: string
}

const props = defineProps<{ tscode: string }>()

const router = useRouter()
const inputCode = ref('')
const years = ref(10)
const loading = ref(false)
const status = ref('')
const cardData = ref<FinanceCardResponse | null>(null)
const showAllPeriods = ref(false)
const includeInventoryInOperatingAssets = ref(true)
const openExplanationIds = ref<Set<string>>(new Set())
const chartEls = new Map<string, HTMLDivElement>()
const charts: ECharts[] = []

const palette = {
  red: '#ff4d55',
  yellow: '#ffc400',
  blue: '#2c91d8',
  purple: '#6b62e9',
  green: '#36b37e',
  teal: '#15b8c8',
  orange: '#c47a2b',
  magenta: '#db35a6',
  gray: '#7b8794',
}

const moduleLabels: Record<string, string> = {
  stock_basic: '股票基础资料缺失',
  finance: '财务三表缺失',
  fina_indicator: '财务指标缺失',
  daily_basic: '日估值/行情缺失',
  fina_mainbz: '主营业务构成缺失',
  balancesheet_payroll_payable: '资产负债表字段 payroll_payable（应付职工薪酬）缺失',
  cashflow_financial_invest: '现金流字段缺失：金融理财投资净额',
  cashflow_production_invest: '现金流字段缺失：生产经营投资净额',
  cashflow_ma_invest: '现金流字段缺失：收购兼并投资净额',
  cashflow_equity_financing: '现金流字段缺失：发行股份筹资净额',
  cashflow_interest_debt_financing: '现金流字段缺失：有息负债筹资净额',
  cashflow_dividend_interest: '现金流字段缺失：支付股息及利息净额',
  cashflow_maintenance_capex: '现金流字段缺失：维持性开支（折旧摊销）',
}

const syncCommands: Record<string, string> = {
  stock_basic: 'uv run python -m app.worker.sync --stock_basic',
  finance: 'uv run python -m app.worker.sync --finance --workers 1',
  fina_indicator: 'uv run python -m app.worker.sync --fina_indicator --workers 1',
  daily_basic: 'uv run python -m app.worker.sync --daily',
  fina_mainbz: 'uv run python -m app.worker.sync --fina_mainbz --mainbz_ts_codes {ts_code} --mainbz_types P --workers 1',
  balancesheet_payroll_payable: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
  cashflow_financial_invest: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
  cashflow_production_invest: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
  cashflow_ma_invest: '本地 cashflow 模型暂无并购投资净额字段，请补模型后同步',
  cashflow_equity_financing: '本地 cashflow 模型暂无发行股份筹资净额字段，请补模型后同步',
  cashflow_interest_debt_financing: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
  cashflow_dividend_interest: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
  cashflow_maintenance_capex: 'uv run python -m app.worker.sync --finance --finance_overwrite --workers 1',
}

const assetStructureRows: FieldSpec[] = [
  {
    label: '固定资产+在建工程',
    cnFields: '固定资产 + （在建工程合计优先，否则在建工程） + 工程物资 + 固定资产清理 + 生产性生物资产 + 油气资产',
    fields: 'fix_assets + (cip_total || cip) + const_materials + fixed_assets_disp + produc_bio_assets + oil_and_gas_assets',
  },
  {
    label: '现金+金融类资产',
    cnFields: '货币资金 + 交易性金融资产 + 拆出资金 + 衍生金融资产 + 买入返售金融资产 + 可供出售金融资产 + 持有至到期投资 + 债权投资 + 其他债权投资 + 其他权益工具投资 + 其他非流动金融资产 + 以公允价值计量且其变动计入当期损益的金融资产 + 以摊余成本计量的金融资产 + 定期存款',
    fields: 'money_cap + trad_asset + loanto_oth_bank_fi + deriv_assets + pur_resale_fa + fa_avail_for_sale + htm_invest + debt_invest + oth_debt_invest + oth_eq_invest + oth_illiq_fin_assets + fair_value_fin_assets + cost_fin_assets + time_deposits',
  },
  {
    label: '投资性房地产',
    cnFields: '投资性房地产',
    fields: 'invest_real_estate',
  },
  {
    label: '长期股权投资',
    cnFields: '长期股权投资',
    fields: 'lt_eqt_invest',
  },
  {
    label: '应收类款项',
    cnFields: '应收票据及应收账款 + 其他应收款 + 应收股利 + 应收利息 + 应收保费 + 应收分保账款 + 应收分保合同准备金 + 应收款项融资',
    fields: 'accounts_receiv_bill + oth_receiv + div_receiv + int_receiv + premium_receiv + reinsur_receiv + reinsur_res_receiv + receiv_financing',
  },
  {
    label: '预付类款项',
    cnFields: '预付款项',
    fields: 'prepayment',
  },
  {
    label: '存货',
    cnFields: '存货',
    fields: 'inventories',
  },
  {
    label: '无形资产',
    cnFields: '无形资产 + 研发支出 + 长期待摊费用',
    fields: 'intan_assets + r_and_d + lt_amor_exp',
  },
  {
    label: '商誉',
    cnFields: '商誉',
    fields: 'goodwill',
  },
  {
    label: '其他资产',
    cnFields: '资产总计 - 以上已归类资产',
    fields: 'total_assets - classified_assets',
  },
]

const capitalStructureRows: FieldSpec[] = [
  {
    label: '有息负债',
    cnFields: '短期借款 + 长期借款 + 一年内到期的非流动负债 + 应付债券 + 向中央银行借款 + 吸收存款及同业存放 + 拆入资金 + 交易性金融负债',
    fields: 'st_borr + lt_borr + non_cur_liab_due_1y + bond_payable + cb_borr + depos_ib_deposits + loan_oth_bank + trading_fl',
  },
  {
    label: '应付类款项',
    cnFields: '应付票据 + 应付账款 + 应付款项',
    fields: 'notes_payable + accounts_payable + acct_payable',
  },
  {
    label: '在手订单',
    cnFields: '预收款项 + 合同负债',
    fields: 'adv_receipts + contract_liab',
  },
  {
    label: '应付职工薪酬+应交税费',
    cnFields: '应付职工薪酬 + 应交税费',
    fields: 'payroll_payable + taxes_payable',
  },
  {
    label: '其他负债',
    cnFields: '负债合计 - 以上已归类负债',
    fields: 'total_liab - classified_liabilities',
  },
  {
    label: '归属母公司股东权益',
    cnFields: '归属于母公司的股东权益',
    fields: 'total_hldr_eqy_exc_min_int',
  },
  {
    label: '少数股东权益',
    cnFields: '少数股东权益',
    fields: 'minority_int',
  },
]

const operatingAssetRows: FieldSpec[] = [
  {
    label: '营运资产',
    cnFields: '应收账款 + 应收票据 + 存货 + 预付款项',
    fields: 'accounts_receiv + notes_receiv + inventories + prepayment',
  },
  {
    label: '营运负债',
    cnFields: '应付账款 + 预收款项 + 合同负债 + 应付职工薪酬 + 应交税费',
    fields: 'acct_payable + adv_receipts + contract_liab + payroll_payable + taxes_payable',
  },
  {
    label: '营运净资产',
    cnFields: '营运资产 - 营运负债',
    fields: 'operating_assets - operating_liabilities',
  },
]

const operatingAssetRowsNoInventory: FieldSpec[] = [
  {
    label: '营运资产（不含存货）',
    cnFields: '应收账款 + 应收票据 + 预付款项',
    fields: 'accounts_receiv + notes_receiv + prepayment',
  },
  operatingAssetRows[1],
  {
    label: '营运净资产（不含存货）',
    cnFields: '营运资产（不含存货） - 营运负债',
    fields: 'operating_assets_no_inventory - operating_liabilities',
  },
]

const profitDistributionRows: FieldSpec[] = [
  {
    label: '主营利润',
    cnFields: '营业收入 - 营业成本 - 税金及附加 - 销售费用 - 管理费用 - 财务费用',
    fields: 'revenue - oper_cost - biz_tax_surchg - sell_exp - admin_exp - fin_exp',
  },
  {
    label: '投资收益',
    cnFields: '投资收益',
    fields: 'invest_income',
  },
  {
    label: '资产减值损益',
    cnFields: '资产减值损失',
    fields: 'assets_impair_loss',
  },
  {
    label: '营业外收支',
    cnFields: '营业外收入 - 营业外支出',
    fields: 'non_oper_income - non_oper_exp',
  },
  {
    label: '其他收益',
    cnFields: '其他收益',
    fields: 'oth_income',
  },
]

const expenseRatioRows: FieldSpec[] = [
  {
    label: '销售费用率',
    cnFields: '销售费用 / 营业总收入',
    fields: 'sell_exp / total_revenue',
  },
  {
    label: '管理费用率',
    cnFields: '管理费用 / 营业总收入',
    fields: 'admin_exp / total_revenue',
  },
  {
    label: '研发费用率',
    cnFields: '研发费用 / 营业总收入',
    fields: 'rd_exp / total_revenue',
  },
  {
    label: '财务费用率',
    cnFields: '财务费用 / 营业总收入',
    fields: 'fin_exp / total_revenue',
  },
  {
    label: '毛利率',
    cnFields: '销售毛利率',
    fields: 'grossprofit_margin',
  },
  {
    label: '净利率',
    cnFields: '销售净利率',
    fields: 'netprofit_margin',
  },
  {
    label: 'ROE',
    cnFields: '净资产收益率',
    fields: 'roe',
  },
  {
    label: '负债率',
    cnFields: '负债合计 / 资产总计',
    fields: 'total_liab / total_assets',
  },
]

const cashflowCapitalAllocationRows: FieldSpec[] = [
  {
    label: 'A. 自我造血：经营现金流',
    cnFields: '经营活动产生的现金流量净额',
    fields: 'n_cashflow_act',
  },
  {
    label: 'B. 维持生存：维持性支出（估算）',
    cnFields: '固定资产折旧 + 无形资产摊销（非现金口径，用作维持性资本开支代理）',
    fields: 'depr_fa_coga_dpba + amort_intang_assets',
  },
  {
    label: 'C. 扩张投入：扩张性CapEx（估算）',
    cnFields: '购建固定资产、无形资产和其他长期资产支付的现金',
    fields: 'c_pay_acq_const_fiolta',
  },
  {
    label: 'D. 金融化：金融理财投资净额',
    cnFields: '收回投资收到的现金 - 投资支付的现金',
    fields: 'c_recp_return_invest - c_paid_invest',
  },
  {
    label: 'E. 外延扩张：并购投资净额',
    cnFields: '处置子公司及其他营业单位收到现金净额 - 取得子公司及其他营业单位支付现金净额',
    fields: 'n_recp_disp_sobu - n_disp_subs_oth_biz',
  },
  {
    label: 'F1. 融资依赖：债务融资净额',
    cnFields: '取得借款 + 发行债券 - 偿还债务',
    fields: 'c_recp_borrow + proc_issue_bonds - c_prepay_amt_borr',
  },
  {
    label: 'F2. 融资依赖：股权融资净额',
    cnFields: '吸收投资收到的现金净额（发行股份/增资）',
    fields: 'c_recp_cap_contrib',
  },
  {
    label: 'G. 股东回报：分红+利息净流出',
    cnFields: '分配股利、利润或偿付利息支付的现金（净流出）',
    fields: '-c_pay_dist_dpcp_int_exp',
  },
]

const cashflowReadingGuide = [
  '读图顺序：1）先看经营现金流（发动机） 2）再看资本开支（维持/扩张） 3）再看融资（债务/股权） 4）最后看投资与并购用途。',
  '经营现金流长期为正且高于净利润，通常代表利润含金量更高；长期低于净利润需警惕应收、存货和回款压力。',
  '维持性开支后自由现金流 = 经营现金流 - 维持性支出；实际自由现金流 = 经营现金流 - 扩张性CapEx。若长期为正，通常资金更自主。',
  '债务融资长期为正且股东回报也高，需核对是否“借新还旧”或“借钱分红”；并购投资大幅波动时应结合商誉与长期股权投资验证质量。',
]

const rawFinanceRows = computed(() => cardData.value?.financeSeries ?? [])
const financeRows = computed(() => {
  const rows = rawFinanceRows.value
  if (showAllPeriods.value) {
    return rows
  }
  const latest = rows[rows.length - 1]
  const filtered = rows.filter(row => row.period?.endsWith('-12-31'))
  if (latest && !latest.period?.endsWith('-12-31') && !filtered.some(row => row.period === latest.period)) {
    filtered.push(latest)
  }
  return filtered
})
const rawValuationRows = computed(() => cardData.value?.valuationSeries ?? [])
const valuationRows = computed(() => {
  const parsed = rawValuationRows.value
    .map((item) => {
      const parsedDate = parseAnyDate(item.tradeDate)
      return parsedDate ? { ...item, _d: parsedDate } : null
    })
    .filter((item): item is (ValuationPoint & { _d: dayjs.Dayjs }) => item !== null)
    .sort((a, b) => a._d.valueOf() - b._d.valueOf())

  if (parsed.length === 0) {
    return []
  }

  const latestYear = parsed[parsed.length - 1]._d.year()
  const startYear = latestYear - 9
  const quarterTargets = [
    { month: 3, day: 31 },
    { month: 6, day: 30 },
    { month: 9, day: 30 },
    { month: 12, day: 31 },
  ]

  const selected: Array<ValuationPoint & { _d: dayjs.Dayjs }> = []
  for (let year = startYear; year <= latestYear; year += 1) {
    for (const target of quarterTargets) {
      const targetDate = dayjs(`${year}-${String(target.month).padStart(2, '0')}-${String(target.day).padStart(2, '0')}`)
      const sameQuarter = parsed.filter(row =>
        row._d.year() === year
        && Math.floor(row._d.month() / 3) === Math.floor((target.month - 1) / 3),
      )
      if (sameQuarter.length === 0) {
        continue
      }
      const exact = sameQuarter.find(row => row._d.isSame(targetDate, 'day'))
      if (exact) {
        selected.push(exact)
        continue
      }
      const after = sameQuarter.filter(row => row._d.isAfter(targetDate)).sort((a, b) => a._d.valueOf() - b._d.valueOf())[0]
      const before = sameQuarter.filter(row => row._d.isBefore(targetDate)).sort((a, b) => b._d.valueOf() - a._d.valueOf())[0]
      selected.push(after || before || sameQuarter[sameQuarter.length - 1])
    }
  }

  const dedup = new Map<string, ValuationPoint>()
  selected.forEach((item) => dedup.set(item.tradeDate, item))
  return Array.from(dedup.values()).sort((a, b) => parseAnyDate(a.tradeDate)!.valueOf() - parseAnyDate(b.tradeDate)!.valueOf())
})
const mainBusinessRows = computed(() => cardData.value?.mainBusinessSeries ?? [])
const missingModules = computed(() => cardData.value?.missingModules ?? [])
const hasFinanceData = computed(() => rawFinanceRows.value.length > 0)
const hasValuationData = computed(() => valuationRows.value.length > 0)
const stockName = computed(() => cardData.value?.stock?.name || inputCode.value)
const stockTitle = computed(() => {
  const stock = cardData.value?.stock
  return stock ? `${stock.name}` : inputCode.value
})
const industryTitle = computed(() => {
  const industry = cardData.value?.industry
  if (industry) {
    return [industry.l1Name, industry.l2Name, industry.l3Name].filter(Boolean).join(' / ')
  }
  return cardData.value?.stock?.industry || '行业数据缺失'
})
const listDate = computed(() => formatDate(cardData.value?.stock?.listDate))
const queriedAt = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'))

const chartSpecs = computed<ChartSpec[]>(() => {
  const specs: ChartSpec[] = []
  const makeSpec = (id: string, option: EChartsOption, className?: string, fieldRows?: FieldSpec[], readingGuide?: string[]): ChartSpec => ({
    id,
    option,
    className,
    fieldRows,
    readingGuide,
  })
  if (hasFinanceData.value) {
    specs.push(
      makeSpec('income-pie', buildIncomePieOption(), 'pie-chart'),
      makeSpec('asset-pie', buildAssetPieOption(), 'pie-chart'),
      makeSpec('valuation-quality', buildValuationQualityOption(), 'wide'),
      makeSpec('asset-structure', buildAssetStructureOption(), 'wide', assetStructureRows),
      makeSpec('capital-structure', buildCapitalStructureOption(), 'wide', capitalStructureRows),
      makeSpec(
        'operating-assets',
        buildOperatingAssetsOption(),
        'wide',
        includeInventoryInOperatingAssets.value ? operatingAssetRows : operatingAssetRowsNoInventory,
      ),
      makeSpec('revenue-cash', buildRevenueCashOption(), 'wide'),
      makeSpec('profit-cash', buildProfitCashOption(), 'wide'),
      makeSpec('profit-distribution', buildProfitDistributionOption(), 'wide', profitDistributionRows),
      makeSpec('expense-ratio', buildExpenseRatioOption(), 'wide', expenseRatioRows),
      makeSpec('cashflow-capital-allocation', buildCashflowCapitalAllocationOption(), 'wide', cashflowCapitalAllocationRows, cashflowReadingGuide),
    )
  }
  if (hasValuationData.value) {
    specs.push(
      makeSpec('pe-price', buildPePriceOption(), 'wide'),
    )
  }
  return specs
})

function normalizeTsCode(raw: string) {
  const value = raw.trim().toUpperCase()
  if (/^\d{6}\.(SZ|SH|BJ)$/.test(value)) {
    return value
  }
  if (/^\d{6}$/.test(value)) {
    if (value.startsWith('6')) {
      return `${value}.SH`
    }
    if (value.startsWith('8') || value.startsWith('9')) {
      return `${value}.BJ`
    }
    return `${value}.SZ`
  }
  return value
}

function formatDate(value?: string | null) {
  if (!value) {
    return '缺失'
  }
  if (value.length === 8) {
    return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6)}`
  }
  return value
}

function parseAnyDate(value?: string | null) {
  if (!value) {
    return null
  }
  if (/^\d{8}$/.test(value)) {
    const normalized = `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
    const d = dayjs(normalized)
    return d.isValid() ? d : null
  }
  const d = dayjs(value)
  return d.isValid() ? d : null
}

function safeNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null
  }
  return Number(value)
}

function toYi(value: number | null | undefined) {
  const n = safeNumber(value)
  return n === null ? null : Number((n / 100000000).toFixed(1))
}

function formatYi(value: number | null | undefined, digits = 2) {
  const yi = toYi(value)
  return yi === null ? '缺失' : `${yi.toFixed(digits)}亿`
}

function toFixedNumber(value: number | null | undefined, digits = 1) {
  const n = safeNumber(value)
  return n === null ? null : Number(n.toFixed(digits))
}

function safeRatio(numerator: number | null | undefined, denominator: number | null | undefined) {
  const n = safeNumber(numerator)
  const d = safeNumber(denominator)
  if (n === null || d === null || d === 0) {
    return null
  }
  return Number(((n / d) * 100).toFixed(1))
}

function positive(value: number | null | undefined) {
  const n = safeNumber(value)
  return n === null ? null : Math.max(n, 0)
}

function financeValue(key: keyof FinanceCardPoint) {
  return financeRows.value.map(item => item[key] as number | null)
}

function valuationValue(key: keyof ValuationPoint) {
  return valuationRows.value.map(item => item[key] as number | null)
}

function financeLabels() {
  return financeRows.value.map(item => item.period)
}

function valuationLabels() {
  return valuationRows.value.map(item => item.tradeDate)
}

function latestFinance() {
  return financeRows.value[financeRows.value.length - 1]
}

function latestMainBusinessPeriod() {
  return mainBusinessRows.value[0]?.period || latestFinance()?.period || ''
}

function syncCommand(moduleName: string) {
  return (syncCommands[moduleName] || moduleName).replace('{ts_code}', cardData.value?.tsCode || inputCode.value)
}

function isExplanationOpen(id: string) {
  return openExplanationIds.value.has(id)
}

function toggleExplanation(id: string) {
  const nextIds = new Set(openExplanationIds.value)
  if (nextIds.has(id)) {
    nextIds.delete(id)
  }
  else {
    nextIds.add(id)
  }
  openExplanationIds.value = nextIds
  nextTick(() => {
    charts.forEach(chart => chart.resize())
  })
}

function toggleOperatingAssetMode() {
  includeInventoryInOperatingAssets.value = !includeInventoryInOperatingAssets.value
  nextTick(() => {
    charts.forEach(chart => chart.resize())
  })
}

function yoy(values: Array<number | null>) {
  return values.map((value, index) => {
    if (index === 0 || value === null || values[index - 1] === null || values[index - 1] === 0) {
      return null
    }
    return Number((((value - Number(values[index - 1])) / Math.abs(Number(values[index - 1]))) * 100).toFixed(1))
  })
}

function disposeCharts() {
  while (charts.length) {
    charts.pop()?.dispose()
  }
}

function setChartEl(id: string, el: Element | ComponentPublicInstance | null) {
  if (el instanceof HTMLDivElement) {
    chartEls.set(id, el)
  }
  else {
    chartEls.delete(id)
  }
}

function initChart(id: string, option: EChartsOption) {
  const el = chartEls.get(id)
  if (!el) {
    return
  }
  const chart = echarts.init(el, undefined, { renderer: 'canvas' })
  chart.setOption(option, true)
  charts.push(chart)
}

function labelFormatter(params: { value?: unknown }) {
  const value = params.value
  if (value === null || value === undefined || Array.isArray(value) || typeof value === 'object') {
    return ''
  }
  return String(value)
}

function baseOption(title: string, unit = '单位:亿元'): EChartsOption {
  return {
    title: {
      text: title,
      left: 'center',
      top: 8,
      textStyle: { color: '#222', fontSize: 16, fontWeight: 700 },
      subtext: unit,
      subtextStyle: { color: '#555', fontSize: 12 },
    },
    color: [palette.red, palette.yellow, palette.blue, palette.purple, palette.green, palette.teal, palette.orange, palette.magenta],
    tooltip: { trigger: 'axis', confine: true },
    toolbox: {
      right: 18,
      top: 10,
      feature: { saveAsImage: { title: '保存' } },
    },
    legend: {
      top: 44,
      left: 'center',
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { color: '#333', fontSize: 11 },
    },
    grid: { left: 70, right: 54, top: 86, bottom: 62 },
    xAxis: {
      type: 'category',
      data: financeLabels(),
      axisLabel: { color: '#555', fontSize: 10, rotate: 0 },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: '#bbb' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 10 },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
    },
  }
}

function lineSeries(name: string, data: Array<number | null>, yAxisIndex = 0, extra: Partial<LineSeriesOption> = {}): LineSeriesOption {
  return {
    name,
    type: 'line',
    smooth: true,
    symbolSize: 5,
    yAxisIndex,
    connectNulls: false,
    label: { show: true, fontSize: 9, formatter: labelFormatter },
    data,
    ...extra,
  }
}

function barSeries(name: string, data: Array<number | null>, extra: Partial<BarSeriesOption> = {}): BarSeriesOption {
  return {
    name,
    type: 'bar',
    barMaxWidth: 22,
    label: { show: true, position: 'top', fontSize: 9, formatter: labelFormatter },
    data,
    ...extra,
  }
}

function stackAreaSeries(name: string, data: Array<number | null>, stack = 'total'): LineSeriesOption {
  return lineSeries(name, data, 0, {
    stack,
    areaStyle: {},
    symbolSize: 3,
    label: { show: false },
  })
}

function pieLabelFormatter(params: { name?: string, value?: unknown, percent?: number }) {
  const value = typeof params.value === 'number' ? params.value : null
  const percent = typeof params.percent === 'number' ? params.percent.toFixed(2) : '--'
  return `${params.name || ''}\n${formatYi(value)}\n${percent}%`
}

function pieTooltipFormatter(metricLabel: string) {
  return (params: { marker?: unknown, name?: string, value?: unknown, percent?: number }) => {
    const value = typeof params.value === 'number' ? params.value : null
    const percent = typeof params.percent === 'number' ? params.percent.toFixed(2) : '--'
    const marker = typeof params.marker === 'string' ? params.marker : ''
    return [
      `${marker}${params.name || ''}`,
      `${metricLabel}：${formatYi(value)}`,
      `占比：${percent}%`,
    ].join('<br/>')
  }
}

function pieSeries(data: Array<{ name: string, value: number }>, metricLabel: string): PieSeriesOption {
  return {
    type: 'pie',
    radius: ['0%', '62%'],
    center: ['50%', '54%'],
    tooltip: {
      trigger: 'item',
      formatter: pieTooltipFormatter(metricLabel),
      confine: true,
    },
    label: {
      formatter: pieLabelFormatter,
      fontSize: 10,
      color: '#222',
    },
    labelLine: { length: 16, length2: 10 },
    data,
  }
}

function mainBusinessPieData(key: keyof Pick<MainBusinessPoint, 'sales' | 'profit'>) {
  const rows = mainBusinessRows.value
    .map(row => ({
      name: row.item || '未披露项目',
      value: Math.max(safeNumber(row[key]) ?? 0, 0),
    }))
    .filter(row => row.value > 0)

  if (rows.length === 0) {
    return [{ name: '主营构成缺失', value: 1 }]
  }

  return rows.sort((a, b) => b.value - a.value)
}

function buildIncomePieOption(): EChartsOption {
  return {
    title: {
      text: `${stockName.value} 收入分布-${latestMainBusinessPeriod()}`,
      left: 'center',
      top: 8,
      textStyle: { color: '#222', fontSize: 15, fontWeight: 500 },
    },
    color: [palette.red, palette.yellow, palette.blue],
    legend: { bottom: 0, left: 'center', itemWidth: 14, itemHeight: 8, textStyle: { fontSize: 11 } },
    toolbox: { right: 12, top: 8, feature: { saveAsImage: { title: '保存' } } },
    tooltip: { trigger: 'item', confine: true },
    series: [pieSeries(mainBusinessPieData('sales'), '主营业务收入')],
  }
}

function buildAssetPieOption(): EChartsOption {
  return {
    title: {
      text: `${stockName.value} 毛利分布-${latestMainBusinessPeriod()}`,
      left: 'center',
      top: 8,
      textStyle: { color: '#222', fontSize: 15, fontWeight: 500 },
    },
    color: [palette.red, palette.yellow, palette.blue, palette.purple],
    legend: { bottom: 0, left: 'center', itemWidth: 14, itemHeight: 8, textStyle: { fontSize: 11 } },
    toolbox: { right: 12, top: 8, feature: { saveAsImage: { title: '保存' } } },
    tooltip: { trigger: 'item', confine: true },
    series: [pieSeries(mainBusinessPieData('profit'), '主营业务毛利')],
  }
}

function buildValuationQualityOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 资产质量和估值数据图（估值数据为年报披露当日估值）`, '单位:值'),
    yAxis: [
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { lineStyle: { color: '#e8e8e8' } } },
      { type: 'value', axisLabel: { formatter: '{value}%', color: '#555', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      barSeries('市净率-TTM', financeValue('pb').map(value => toFixedNumber(value))),
      barSeries('市盈率-TTM', financeValue('pe').map(value => toFixedNumber(value))),
      lineSeries('净资产收益率', financeValue('roe').map(value => toFixedNumber(value)), 1),
      lineSeries('总资产收益率', financeRows.value.map(item => safeRatio(item.netProfit, item.totalAssets)), 1),
    ],
  }
}

function buildAssetStructureOption(): EChartsOption {
  const money = financeValue('moneyCap').map(toYi)
  const totalAssets = financeValue('totalAssets').map(toYi)
  const fixedAssets = financeValue('fixedAssets').map(toYi)
  const financialAssets = financeValue('financialAssets').map(toYi)
  const investRealEstate = financeValue('investRealEstate').map(toYi)
  const longEquityInvestment = financeValue('longEquityInvestment').map(toYi)
  const receivables = financeValue('receivables').map(toYi)
  const prepaidAssets = financeValue('prepaidAssets').map(toYi)
  const inventories = financeValue('inventories').map(toYi)
  const intangibleAssets = financeValue('intangibleAssets').map(toYi)
  const goodwill = financeValue('goodwill').map(toYi)
  const otherAssets = totalAssets.map((value, index) => {
    if (value === null) {
      return null
    }
    return Number(Math.max(
      value
      - (money[index] ?? 0)
      - (fixedAssets[index] ?? 0)
      - (financialAssets[index] ?? 0)
      - (investRealEstate[index] ?? 0)
      - (longEquityInvestment[index] ?? 0)
      - (receivables[index] ?? 0)
      - (prepaidAssets[index] ?? 0)
      - (inventories[index] ?? 0)
      - (intangibleAssets[index] ?? 0)
      - (goodwill[index] ?? 0),
      0,
    ).toFixed(1))
  })
  return {
    ...baseOption(`${stockName.value} 资产结构图（亿元）`),
    series: [
      stackAreaSeries('固定资产+在建工程', fixedAssets),
      stackAreaSeries('现金+金融类资产', money.map((value, index) => Number(((value ?? 0) + (financialAssets[index] ?? 0)).toFixed(1)))),
      stackAreaSeries('投资性房地产', investRealEstate),
      stackAreaSeries('长期股权投资', longEquityInvestment),
      stackAreaSeries('应收类款项', receivables),
      stackAreaSeries('预付类款项', prepaidAssets),
      stackAreaSeries('存货', inventories),
      stackAreaSeries('无形资产', intangibleAssets),
      stackAreaSeries('商誉', goodwill),
      stackAreaSeries('其他资产', otherAssets),
      lineSeries('资产合计', totalAssets, 0, { label: { show: false }, lineStyle: { width: 2 } }),
    ],
  }
}

function buildCapitalStructureOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 负债 + 股东权益结构图（亿元）`),
    series: [
      stackAreaSeries('有息负债', financeValue('interestBearingDebt').map(toYi)),
      stackAreaSeries('应付类款项', financeValue('payables').map(toYi)),
      stackAreaSeries('在手订单', financeValue('contractLiabilities').map(toYi)),
      stackAreaSeries('应付职工薪酬+应交税费', financeValue('employeeTaxPayables').map(toYi)),
      stackAreaSeries('其他负债', financeValue('otherLiabilities').map(toYi)),
      stackAreaSeries('归属母公司股东权益', financeValue('parentEquity').map(toYi)),
      stackAreaSeries('少数股东权益', financeValue('minorityEquity').map(toYi)),
    ],
  }
}

function buildOperatingAssetsOption(): EChartsOption {
  const operatingAssetsWithInventory = financeValue('operatingAssets').map(toYi)
  const inventories = financeValue('inventories').map(toYi)
  const operatingAssets = operatingAssetsWithInventory.map((value, index) => {
    if (value === null) {
      return null
    }
    if (includeInventoryInOperatingAssets.value) {
      return value
    }
    return Number((value - (inventories[index] ?? 0)).toFixed(1))
  })
  const operatingLiabilities = financeValue('operatingLiabilities').map(toYi)
  const operatingNetAssets = operatingAssets.map((value, index) => {
    if (value === null || operatingLiabilities[index] === null) {
      return null
    }
    return Number((value - Number(operatingLiabilities[index])).toFixed(1))
  })
  return {
    ...baseOption(`${stockName.value} 营运净资产变化（亿元）`),
    series: [
      barSeries(
        includeInventoryInOperatingAssets.value ? '营运资产' : '营运资产（不含存货）',
        operatingAssets,
        { itemStyle: { color: palette.yellow } },
      ),
      barSeries('营运负债', operatingLiabilities, { itemStyle: { color: palette.orange } }),
      barSeries(
        includeInventoryInOperatingAssets.value ? '营运净资产' : '营运净资产（不含存货）',
        operatingNetAssets,
        { itemStyle: { color: palette.red } },
      ),
    ],
  }
}

function buildRevenueCashOption(): EChartsOption {
  const totalRevenue = financeValue('totalRevenue').map(toYi)
  return {
    ...baseOption(`${stockName.value} 营业总收入 和 销售商品、提供劳务收到的现金变化（亿元）`),
    yAxis: [
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { lineStyle: { color: '#e8e8e8' } } },
      { type: 'value', axisLabel: { formatter: '{value}%', color: '#555', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      barSeries('营业总收入', totalRevenue),
      barSeries('销售商品、提供劳务收到的现金', financeValue('salesGoodsCash').map(toYi), { itemStyle: { color: palette.yellow } }),
      lineSeries('现金收入占营业总收入比率', financeRows.value.map(item => safeRatio(item.salesGoodsCash, item.totalRevenue)), 1),
      lineSeries('营业总收入同比增长率', yoy(totalRevenue), 1),
    ],
  }
}

function buildProfitCashOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 净利润 和 经营活动收到的现金流净额变化（亿元）`),
    yAxis: [
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { lineStyle: { color: '#e8e8e8' } } },
      { type: 'value', axisLabel: { formatter: '{value}%', color: '#555', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      barSeries('净利润', financeValue('nIncome').map(toYi)),
      barSeries('经营现金流', financeValue('operatingCashFlow').map(toYi)),
      lineSeries('净利润现金比率', financeRows.value.map(item => safeRatio(item.operatingCashFlow, item.nIncome)), 1),
      lineSeries('净利润同比增长率', yoy(financeValue('nIncome').map(toYi)), 1),
    ],
  }
}

function buildProfitDistributionOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 税前利润分布（亿元）`),
    color: ['#ff4d55', '#f4bf00', '#84cc16', '#10b981', '#60739b'],
    series: [
      barSeries('主营利润', financeValue('mainBusinessProfit').map(toYi), { itemStyle: { color: '#ff4d55' } }),
      barSeries('投资收益', financeValue('investIncome').map(toYi), { itemStyle: { color: '#f4bf00' } }),
      barSeries('资产减值损益', financeValue('assetsImpairLoss').map(toYi), { itemStyle: { color: '#84cc16' } }),
      barSeries('营业外收支', financeValue('nonOperatingBalance').map(toYi), { itemStyle: { color: '#10b981' } }),
      barSeries('其他收益', financeValue('otherIncome').map(toYi), { itemStyle: { color: '#60739b' } }),
    ],
  }
}

function buildExpenseRatioOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 历年期间费用率`, '单位:%'),
    series: [
      lineSeries('销售费用率', financeValue('salesExpenseRatio').map(value => toFixedNumber(value)), 0, { label: { show: false } }),
      lineSeries('管理费用率', financeValue('adminExpenseRatio').map(value => toFixedNumber(value)), 0, { label: { show: false } }),
      lineSeries('研发费用率', financeValue('rdExpenseRatio').map(value => toFixedNumber(value)), 0, { label: { show: false } }),
      lineSeries('财务费用率', financeValue('financeExpenseRatio').map(value => toFixedNumber(value)), 0, { label: { show: false } }),
      lineSeries('毛利率', financeValue('grossMargin').map(value => toFixedNumber(value)), 0, { lineStyle: { width: 3 } }),
      lineSeries('净利率', financeValue('netProfitMargin').map(value => toFixedNumber(value))),
      lineSeries('ROE', financeValue('roe').map(value => toFixedNumber(value))),
      lineSeries('负债率', financeRows.value.map(item => safeRatio(item.totalLiab, item.totalAssets))),
    ],
  }
}

function buildCashflowCapitalAllocationOption(): EChartsOption {
  const maintenanceCapex = financeValue('maintenanceCapex').map(toYi)
  const actualCapex = financeValue('actualCapex').map(toYi)
  const freeCashflowAfterMaintenance = financeValue('freeCashFlowAfterMaintenance').map(toYi)
  const actualFreeCashflow = financeValue('actualFreeCashFlow').map(toYi)
  return {
    ...baseOption(`${stockName.value} 现金流资本配置总览（亿元）`),
    yAxis: [
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { lineStyle: { color: '#e8e8e8' } } },
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      barSeries('经营现金流', financeValue('operatingCashFlow').map(toYi), { itemStyle: { color: palette.red } }),
      barSeries('维持性支出(估算)', maintenanceCapex.map(value => (value === null ? null : Number((-value).toFixed(1)))), { itemStyle: { color: palette.yellow } }),
      barSeries('扩张性CapEx(估算)', actualCapex.map(value => (value === null ? null : Number((-value).toFixed(1)))), { itemStyle: { color: palette.orange } }),
      barSeries('金融投资净额', financeValue('financialWealthInvestNet').map(toYi), { itemStyle: { color: palette.green } }),
      barSeries('并购投资净额', financeValue('maInvestNet').map(toYi), { itemStyle: { color: palette.teal } }),
      barSeries('债务融资净额', financeValue('interestDebtFinancingNet').map(toYi), { itemStyle: { color: palette.blue } }),
      barSeries('股权融资净额', financeValue('equityFinancingNet').map(toYi), { itemStyle: { color: palette.magenta } }),
      barSeries('股东回报净额', financeValue('dividendInterestPaymentNet').map(toYi), { itemStyle: { color: palette.purple } }),
      lineSeries('维持性开支后自由现金流', freeCashflowAfterMaintenance, 1, { lineStyle: { width: 2 }, label: { show: false } }),
      lineSeries('实际自由现金流', actualFreeCashflow, 1, { lineStyle: { width: 2 }, label: { show: false } }),
    ],
  }
}

function buildPePriceOption(): EChartsOption {
  return {
    ...baseOption(`${stockName.value} 近10年财报期估值与股价（3/31、6/30、9/30、12/31）`, '单位:值'),
    xAxis: {
      type: 'category',
      data: valuationLabels(),
      axisLabel: { color: '#555', fontSize: 10, rotate: 28 },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: '#bbb' } },
    },
    yAxis: [
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { lineStyle: { color: '#e8e8e8' } } },
      { type: 'value', axisLabel: { color: '#555', fontSize: 10 }, splitLine: { show: false } },
    ],
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 20 }],
    grid: { left: 70, right: 54, top: 86, bottom: 88 },
    series: [
      barSeries('市盈率-TTM', valuationValue('pe').map(value => toFixedNumber(value)), { itemStyle: { color: palette.yellow } }),
      barSeries('市销率-TTM', valuationValue('ps').map(value => toFixedNumber(value)), { itemStyle: { color: palette.green } }),
      barSeries('市净率-TTM', valuationValue('pb').map(value => toFixedNumber(value)), { itemStyle: { color: palette.purple } }),
      lineSeries('股价', valuationValue('close').map(value => toFixedNumber(value)), 1),
    ],
  }
}

async function renderCharts() {
  await nextTick()
  disposeCharts()
  chartSpecs.value.forEach(spec => initChart(spec.id, spec.option))
}

async function loadCard(code = inputCode.value) {
  const normalizedCode = normalizeTsCode(code)
  if (!normalizedCode) {
    status.value = '请输入股票代码'
    return
  }
  loading.value = true
  status.value = '加载中...'
  inputCode.value = normalizedCode
  try {
    const res = await getFinanceCard(normalizedCode, years.value)
    cardData.value = res.data
    queriedAt.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
    status.value = ''
    await renderCharts()
  }
  catch (error) {
    cardData.value = null
    disposeCharts()
    status.value = '网络或服务错误'
    console.error(error)
  }
  finally {
    loading.value = false
  }
}

function queryCard() {
  const normalizedCode = normalizeTsCode(inputCode.value)
  router.push(`/stock/${encodeURIComponent(normalizedCode)}/card`)
}

function resizeCharts() {
  charts.forEach(chart => chart.resize())
}

watch(() => props.tscode, (value) => {
  inputCode.value = normalizeTsCode(value)
  loadCard(inputCode.value)
}, { immediate: true })

watch(years, () => loadCard(inputCode.value))

watch(chartSpecs, () => renderCharts(), { flush: 'post' })

window.addEventListener('resize', resizeCharts)
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>

<template>
  <main class="report-page">
    <header class="report-header">
      <h1>欢迎使用财务卡片小助手（毛坯版）</h1>
      <div class="search-line">
        <input v-model="inputCode" placeholder="请输入股票代码" @keyup.enter="queryCard">
        <button :disabled="loading" @click="queryCard">
          获取财务卡片
        </button>
        <router-link class="table-link" :to="`/stock/${encodeURIComponent(inputCode)}`">
          返回财务表
        </router-link>
      </div>
      <p>本次检索时间：{{ queriedAt }}，如30秒内未展示相应卡片，请确认本地后端和数据库数据。</p>
      <p>本次查询代码：<b>{{ cardData?.tsCode || inputCode }}</b>，股票名称：<b>{{ stockTitle }}</b>，股票上市时间：{{ listDate }}</p>
      <p class="industry-line">{{ industryTitle }}</p>
      <label class="period-toggle">
        <input v-model="showAllPeriods" type="checkbox">
        显示全部季度数据
      </label>
      <p class="period-hint">
        {{ showAllPeriods ? '当前显示全部财报期间。' : '当前仅显示历年12月31日年报数据，并保留今年最新季度。' }}
      </p>
    </header>

    <section v-if="status || missingModules.length" class="notice">
      <strong>{{ status || '本地数据不完整' }}</strong>
      <template v-if="missingModules.length">
        <p>缺失模块：{{ missingModules.map(item => moduleLabels[item] || item).join('、') }}</p>
        <div class="commands">
          <code v-for="item in missingModules" :key="item">{{ syncCommand(item) }}</code>
        </div>
        <p>同步需要可用的 TUSHARE_TOKEN 和相应接口权限；页面不会自动补数或添加伪数据。</p>
      </template>
    </section>

    <section class="chart-report">
      <article
        v-for="spec in chartSpecs"
        :key="spec.id"
        class="chart-card"
        :class="spec.className"
      >
        <div
          :ref="el => setChartEl(spec.id, el)"
          class="chart-block"
        />
        <div v-if="spec.fieldRows?.length || spec.id === 'operating-assets'" class="chart-explain-bar">
          <button
            v-if="spec.id === 'operating-assets'"
            type="button"
            class="chart-explain-toggle"
            @click="toggleOperatingAssetMode"
          >
            {{ includeInventoryInOperatingAssets ? '切换为不含存货' : '切换为含存货' }}
          </button>
          <button type="button" class="chart-explain-toggle" @click="toggleExplanation(spec.id)">
            {{ isExplanationOpen(spec.id) ? '收起字段口径' : '查看字段口径' }}
          </button>
        </div>
        <div v-if="spec.fieldRows?.length && isExplanationOpen(spec.id)" class="chart-field-table">
          <table>
            <thead>
              <tr>
                <th>图表展示名称</th>
                <th>中文字段</th>
                <th>Tushare 字段名</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in spec.fieldRows" :key="row.label">
                <td>{{ row.label }}</td>
                <td>{{ row.cnFields }}</td>
                <td><code>{{ row.fields }}</code></td>
              </tr>
            </tbody>
          </table>
          <div v-if="spec.readingGuide?.length" class="reading-guide">
            <h3>阅读顺序与解读要点</h3>
            <p v-for="line in spec.readingGuide" :key="line">{{ line }}</p>
          </div>
        </div>
      </article>
      <div v-if="!hasFinanceData && !loading" class="empty-panel">
        财务三表缺失，无法展示财务小卡片主体图表。
      </div>
      <div v-if="!hasValuationData && !loading" class="empty-panel">
        日估值/行情缺失，无法展示 PE、PB 与股价图。
      </div>
    </section>

  </main>
</template>

<style scoped>
.report-page {
  background: #fff;
  color: #111;
  font-family: Arial, 'Microsoft YaHei', sans-serif;
  min-height: 100%;
  overflow-y: auto;
  padding: 8px 0 24px;
}

.report-header {
  margin: 0 auto;
  text-align: center;
  width: min(1000px, calc(100vw - 20px));
}

.report-header h1 {
  font-size: 16px;
  line-height: 1.4;
  margin-bottom: 6px;
}

.search-line {
  align-items: center;
  display: flex;
  gap: 0;
  justify-content: center;
  margin-bottom: 6px;
}

.search-line input {
  border: 1px solid #999;
  border-radius: 0;
  font-size: 13px;
  height: 26px;
  padding: 0 8px;
  width: 260px;
}

.search-line button,
.table-link {
  align-items: center;
  background: #efefef;
  border: 1px solid #777;
  border-left: 0;
  border-radius: 0;
  color: #111;
  cursor: pointer;
  display: inline-flex;
  font-size: 13px;
  font-weight: 700;
  height: 26px;
  justify-content: center;
  min-width: 120px;
  padding: 0 10px;
  text-decoration: none;
}

.search-line button:disabled {
  color: #888;
  cursor: not-allowed;
}

.report-header p {
  font-size: 16px;
  line-height: 1.45;
}

.industry-line {
  color: #333;
  font-size: 13px !important;
}

.period-toggle {
  align-items: center;
  display: inline-flex;
  gap: 6px;
  font-size: 13px;
  margin-top: 6px;
}

.period-toggle input {
  height: 14px;
  width: 14px;
}

.period-hint {
  color: #555;
  font-size: 12px !important;
}

.notice {
  background: #fff8ec;
  border: 1px solid #f5c27a;
  color: #8a4a00;
  font-size: 13px;
  margin: 10px auto 0;
  padding: 10px 12px;
  width: min(1000px, calc(100vw - 20px));
}

.notice p {
  margin-top: 5px;
}

.commands {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 8px;
}

code {
  background: #ffe8c2;
  border-radius: 3px;
  color: #6d3200;
  padding: 3px 6px;
}

.chart-report {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 8px auto 0;
  row-gap: 10px;
  width: min(1000px, calc(100vw - 20px));
}

.chart-card {
  min-width: 0;
  width: 100%;
}

.chart-block {
  background: #fff;
  height: 430px;
  min-width: 0;
  width: 100%;
}

.pie-chart .chart-block {
  height: 360px;
}

.wide {
  grid-column: 1 / -1;
}

.wide .chart-block {
  height: 500px;
}

.chart-explain-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: -22px;
  padding-right: 24px;
  position: relative;
  z-index: 1;
}

.chart-explain-toggle {
  background: #f5f5f5;
  border: 1px solid #aaa;
  border-radius: 2px;
  color: #333;
  cursor: pointer;
  font-size: 12px;
  height: 24px;
  line-height: 22px;
  padding: 0 10px;
}

.chart-explain-toggle:hover {
  background: #eee;
}

.chart-field-table {
  background: #fafafa;
  border: 1px solid #d8d8d8;
  color: #333;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 24px 4px;
  padding: 8px 10px;
}

.empty-panel {
  align-items: center;
  border: 1px solid #ddd;
  color: #666;
  display: flex;
  font-size: 15px;
  grid-column: 1 / -1;
  height: 180px;
  justify-content: center;
}

.chart-field-table table {
  border-collapse: collapse;
  font-size: 11px;
  line-height: 1.45;
  width: 100%;
}

.chart-field-table th,
.chart-field-table td {
  border: 1px solid #d8d8d8;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}

.chart-field-table th {
  background: #f5f5f5;
  text-align: center;
}

.chart-field-table td:first-child {
  font-weight: 700;
  white-space: nowrap;
  width: 140px;
}

.chart-field-table code {
  background: transparent;
  color: #333;
  font-family: Consolas, 'Courier New', monospace;
  padding: 0;
}

.reading-guide {
  border-top: 1px dashed #d0d0d0;
  margin-top: 8px;
  padding-top: 8px;
}

.reading-guide h3 {
  font-size: 13px;
  margin-bottom: 4px;
}

.reading-guide p {
  font-size: 12px;
  line-height: 1.6;
}

.report-footer {
  color: #333;
  font-size: 13px;
  margin: 16px auto 0;
  text-align: center;
  width: min(1000px, calc(100vw - 20px));
}

.report-footer a {
  color: #1d4ed8;
}

@media (max-width: 760px) {
  .chart-report {
    grid-template-columns: 1fr;
  }

  .wide {
    grid-column: 1;
  }

  .search-line {
    flex-wrap: wrap;
  }

  .search-line button,
  .table-link {
    border-left: 1px solid #777;
    margin-top: 4px;
  }
}
</style>
