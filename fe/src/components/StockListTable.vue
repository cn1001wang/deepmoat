<script setup lang="ts">
import { AgGridVue } from 'ag-grid-vue3'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ColDef, FilterChangedEvent, GridReadyEvent } from 'ag-grid-community'
import type { AnnualMetricSeries, Stock } from '@/api/finance'

const props = defineProps<{
  data: Stock[]
}>()

const router = useRouter()

// 1. 定义存储标识
const STORAGE_KEY = 'stock-list-filter-state'
const gridApi = ref<any>(null)

// 2. 筛选变化时保存状态
function onFilterChanged(event: FilterChangedEvent) {
  const filterModel = event.api.getFilterModel()
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filterModel))
}

// 3. 表格就绪时恢复状态
function onGridReady(params: GridReadyEvent) {
  gridApi.value = params.api

  const savedFilterModel = localStorage.getItem(STORAGE_KEY)
  if (savedFilterModel) {
    try {
      const model = JSON.parse(savedFilterModel)
      // 应用保存的筛选模型
      params.api.setFilterModel(model)
    }
    catch (e) {
      console.error('解析缓存的筛选项失败', e)
    }
  }
}

/**
 * 核心逻辑：隐藏重复的单元格文字
 * 使用 previousSibling 避开 Grid API 渲染冲突错误 #252
 */
const cellClassRules = {
  'cell-span-hidden': (params: any) => {
    const field = params.colDef.field as keyof Stock
    const value = params.value
    // 直接通过节点链表获取上一行，不触发 API 重绘
    const prevNode = params.node.previousSibling
    return prevNode && value === prevNode.data?.[field]
  },
}

type AnnualMetricKey = 'revenue' | 'netProfit' | 'operatingCashFlow' | 'grossMargin'

const annualMetricColumnMeta: Array<{
  headerName: string
  key: AnnualMetricKey
  color: string
  unit: 'yuan' | 'percent'
}> = [
  { headerName: '营业收入数据', key: 'revenue', color: '#7c3aed', unit: 'yuan' },
  { headerName: '净利润数据', key: 'netProfit', color: '#ef4444', unit: 'yuan' },
  { headerName: '经营净现金数据', key: 'operatingCashFlow', color: '#f59e0b', unit: 'yuan' },
  { headerName: '毛利率数据', key: 'grossMargin', color: '#0891b2', unit: 'percent' },
]

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function formatAnnualMetricValue(value: number | null, unit: 'yuan' | 'percent') {
  if (!isFiniteNumber(value))
    return '暂无数据'
  if (unit === 'percent')
    return `${value.toFixed(2)}%`
  return `${(value / 100000000).toFixed(2)}亿`
}

function findLatestAnnualMetric(values: Array<number | null>, years: number[]) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    const value = values[index]
    if (isFiniteNumber(value)) {
      return {
        year: years[index],
        value,
      }
    }
  }
  return null
}

function createAnnualBarCell(series: AnnualMetricSeries | undefined, key: AnnualMetricKey, color: string, unit: 'yuan' | 'percent') {
  const values = series?.[key] || Array.from<number | null>({ length: 10 }).fill(null)
  const years = series?.years || []
  const numericValues = values.filter(isFiniteNumber)
  const min = numericValues.length ? Math.min(0, ...numericValues) : 0
  const max = numericValues.length ? Math.max(0, ...numericValues) : 0
  const span = max - min || 1
  const zeroY = max <= 0 ? 0 : min >= 0 ? 1 : max / span
  const valueToY = (value: number) => (max - value) / span

  const root = document.createElement('div')
  root.className = 'annual-bar-cell'
  root.title = values.map((value, index) => {
    const year = years[index] || ''
    return `${year}: ${formatAnnualMetricValue(value, unit)}`
  }).join('\n')

  const latestMetric = findLatestAnnualMetric(values, years)
  const latest = document.createElement('span')
  latest.className = 'annual-bar-latest'
  latest.textContent = latestMetric
    ? `${latestMetric.year || ''} ${formatAnnualMetricValue(latestMetric.value, unit)}`
    : '暂无数据'
  root.appendChild(latest)

  values.forEach((value) => {
    const slot = document.createElement('span')
    slot.className = 'annual-bar-slot'

    const bar = document.createElement('span')
    bar.className = 'annual-bar'

    if (isFiniteNumber(value)) {
      const valueY = valueToY(value)
      const start = Math.min(zeroY, valueY)
      const end = Math.max(zeroY, valueY)
      const top = Math.max(0, Math.min(1, start)) * 100
      const height = Math.max(2, Math.max(0.02, end - start) * 100)
      bar.style.top = `${top}%`
      bar.style.height = `${height}%`
      bar.style.background = value < 0 ? '#22c55e' : color
    }
    else {
      bar.classList.add('annual-bar-placeholder')
    }

    slot.appendChild(bar)
    root.appendChild(slot)
  })

  return root
}

const annualMetricColumns: ColDef[] = annualMetricColumnMeta.map(meta => ({
  headerName: meta.headerName,
  colId: `annual_${meta.key}`,
  width: 190,
  minWidth: 150,
  sortable: false,
  filter: false,
  cellClass: 'annual-bar-grid-cell',
  cellRenderer: (params: any) => createAnnualBarCell(params.data?.annualMetrics, meta.key, meta.color, meta.unit),
}))

const finaIndicatorColumns = [
  { headerName: '收盘价', field: 'close' },
  { headerName: 'ROE(%)', field: 'roe' },
  { headerName: '总市值（亿元）', field: 'totalMv' },
  { headerName: '市盈率', field: 'pe' },
  { headerName: '市盈率ttm', field: 'peTtm' },
  { headerName: '换手率（%）', field: 'turnoverRate' },
  { headerName: '市净率', field: 'pb' },
  { headerName: '市销率', field: 'ps' },
  { headerName: '市销率（TTM）', field: 'psTtm' },
  { headerName: '股息率（%）', field: 'dvRatio' },
  { headerName: '股息率（TTM）（%） ', field: 'dvTtm' },
  { headerName: '总股本（万股） ', field: 'totalShare' },
  { headerName: '流通股本（万股）', field: 'floatShare' },
  { headerName: '自由流通股本（万）', field: 'freeShare' },
  { headerName: '流通市值（万元）', field: 'circMv' },
  { headerName: '年化净资产收益率', field: 'roeYearly' },
  { headerName: '年化总资产报酬率', field: 'roa2Yearly' },
  { headerName: '净资产收益率(扣除非经常损益)', field: 'roeDt' },
  { headerName: 'ROIC', field: 'roic' },
  { headerName: '扣非净利润', field: 'profitDedt' },
  { headerName: '销售净利率', field: 'netprofitMargin' },
  { headerName: '销售毛利率', field: 'grossprofitMargin' },
  { headerName: '经营活动产生的现金流量净额/营业收入', field: 'ocfToOr' },
  { headerName: '资产负债率', field: 'debtToAssets' },
  // 新增重点关注字段
  { headerName: '基本每股收益', field: 'eps' },
  { headerName: '稀释每股收益', field: 'dtEps' },
  { headerName: '每股营业总收入', field: 'totalRevenuePs' },
  { headerName: '每股营业收入', field: 'revenuePs' },
  { headerName: '每股资本公积', field: 'capitalResePs' },
  { headerName: '每股盈余公积', field: 'surplusResePs' },
  { headerName: '每股未分配利润', field: 'undistProfitPs' },
  { headerName: '非经常性损益', field: 'extraItem' },
  { headerName: '毛利', field: 'grossMargin' },
  { headerName: '流动比率', field: 'currentRatio' },
  { headerName: '速动比率', field: 'quickRatio' },
  { headerName: '保守速动比率', field: 'cashRatio' },
  { headerName: '存货周转天数', field: 'invturnDays' },
  { headerName: '应收账款周转天数', field: 'arturnDays' },
  { headerName: '存货周转率', field: 'invTurn' },
  { headerName: '应收账款周转率', field: 'arTurn' },
  { headerName: '流动资产周转率', field: 'caTurn' },
  { headerName: '固定资产周转率', field: 'faTurn' },
  { headerName: '总资产周转率', field: 'assetsTurn' },
  { headerName: '经营活动净收益', field: 'opIncome' },
  { headerName: '价值变动净收益', field: 'valuechangeIncome' },
  { headerName: '利息费用', field: 'interstIncome' },
  { headerName: '折旧与摊销', field: 'daa' },
  { headerName: '息税前利润', field: 'ebit' },
  { headerName: '息税折旧摊销前利润', field: 'ebitda' },
  { headerName: '企业自由现金流量', field: 'fcff' },
  { headerName: '股权自由现金流量', field: 'fcfe' },
  { headerName: '无息流动负债', field: 'currentExint' },
  { headerName: '无息非流动负债', field: 'noncurrentExint' },
  { headerName: '带息债务', field: 'interestdebt' },
  { headerName: '净债务', field: 'netdebt' },
  { headerName: '有形资产', field: 'tangibleAsset' },
  { headerName: '营运资金', field: 'workingCapital' },
  { headerName: '营运流动资本', field: 'networkingCapital' },
  { headerName: '全部投入资本', field: 'investCapital' },
  { headerName: '留存收益', field: 'retainedEarnings' },
  { headerName: '期末摊薄每股收益', field: 'diluted2Eps' },
  { headerName: '每股净资产', field: 'bps' },
  { headerName: '每股经营活动产生的现金流量净额', field: 'ocfps' },
  { headerName: '每股留存收益', field: 'retainedps' },
  { headerName: '每股现金流量净额', field: 'cfps' },
  { headerName: '每股息税前利润', field: 'ebitPs' },
  { headerName: '每股企业自由现金流量', field: 'fcffPs' },
  { headerName: '每股股东自由现金流量', field: 'fcfePs' },
  { headerName: '销售成本率', field: 'cogsOfSales' },
  { headerName: '销售期间费用率', field: 'expenseOfSales' },
  { headerName: '净利润/营业总收入', field: 'profitToGr' },
  { headerName: '销售费用/营业总收入', field: 'saleexpToGr' },
  { headerName: '管理费用/营业总收入', field: 'adminexpOfGr' },
  { headerName: '财务费用/营业总收入', field: 'finaexpOfGr' },
  { headerName: '资产减值损失/营业总收入', field: 'impaiTtm' },
  { headerName: '营业总成本/营业总收入', field: 'gcOfGr' },
  { headerName: '营业利润/营业总收入', field: 'opOfGr' },
  { headerName: '息税前利润/营业总收入', field: 'ebitOfGr' },
  { headerName: '加权平均净资产收益率', field: 'roeWaa' },
  { headerName: '总资产报酬率', field: 'roa' },
  { headerName: '总资产净利润', field: 'npta' },
  { headerName: '经营活动净收益/利润总额', field: 'opincomeOfEbt' },
  { headerName: '价值变动净收益/利润总额', field: 'investincomeOfEbt' },
  { headerName: '营业外收支净额/利润总额', field: 'nOpProfitOfEbt' },
  { headerName: '所得税/利润总额', field: 'taxToEbt' },
  { headerName: '扣除非经常损益后的净利润/净利润', field: 'dtprofitToProfit' },
  { headerName: '销售商品提供劳务收到的现金/营业收入', field: 'salescashToOr' },
  { headerName: '经营活动产生的现金流量净额/经营活动净收益', field: 'ocfToOpincome' },
  { headerName: '资本支出/折旧和摊销', field: 'capitalizedToDa' },
  { headerName: '权益乘数', field: 'assetsToEqt' },
  { headerName: '权益乘数(杜邦分析)', field: 'dpAssetsToEqt' },
  { headerName: '流动资产/总资产', field: 'caToAssets' },
  { headerName: '非流动资产/总资产', field: 'ncaToAssets' },
  { headerName: '有形资产/总资产', field: 'tbassetsToTotalassets' },
  { headerName: '带息债务/全部投入资本', field: 'intToTalcap' },
  { headerName: '归属于母公司的股东权益/全部投入资本', field: 'eqtToTalcapital' },
  { headerName: '流动负债/负债合计', field: 'currentdebtToDebt' },
  { headerName: '非流动负债/负债合计', field: 'longdebToDebt' },
  { headerName: '经营活动产生的现金流量净额/流动负债', field: 'ocfToShortdebt' },
  { headerName: '产权比率', field: 'debtToEqt' },
  { headerName: '归属于母公司的股东权益/负债合计', field: 'eqtToDebt' },
  { headerName: '归属于母公司的股东权益/带息债务', field: 'eqtToInterestdebt' },
  { headerName: '有形资产/负债合计', field: 'tangibleassetToDebt' },
  { headerName: '有形资产/带息债务', field: 'tangassetToIntdebt' },
  { headerName: '有形资产/净债务', field: 'tangibleassetToNetdebt' },
  { headerName: '经营活动产生的现金流量净额/负债合计', field: 'ocfToDebt' },
  { headerName: '经营活动产生的现金流量净额/带息债务', field: 'ocfToInterestdebt' },
  { headerName: '经营活动产生的现金流量净额/净债务', field: 'ocfToNetdebt' },
  { headerName: '已获利息倍数', field: 'ebitToInterest' },
  { headerName: '长期债务与营运资金比率', field: 'longdebtToWorkingcapital' },
  { headerName: '息税折旧摊销前利润/负债合计', field: 'ebitdaToDebt' },
  { headerName: '营业周期', field: 'turnDays' },
  { headerName: '年化总资产净利率', field: 'roaYearly' },
  { headerName: '总资产净利率(杜邦分析)', field: 'roaDp' },
  { headerName: '固定资产合计', field: 'fixedAssets' },
  { headerName: '扣除财务费用前营业利润', field: 'profitPrefinExp' },
  { headerName: '非营业利润', field: 'nonOpProfit' },
  { headerName: '营业利润／利润总额', field: 'opToEbt' },
  { headerName: '非营业利润／利润总额', field: 'nopToEbt' },
  { headerName: '经营活动产生的现金流量净额／营业利润', field: 'ocfToProfit' },
  { headerName: '货币资金／流动负债', field: 'cashToLiqdebt' },
  { headerName: '货币资金／带息流动负债', field: 'cashToLiqdebtWithinterest' },
  { headerName: '营业利润／流动负债', field: 'opToLiqdebt' },
  { headerName: '营业利润／负债合计', field: 'opToDebt' },
  { headerName: '年化投入资本回报率', field: 'roicYearly' },
  { headerName: '固定资产合计周转率', field: 'totalFaTrun' },
  { headerName: '利润总额／营业收入', field: 'profitToOp' },
  { headerName: '经营活动单季度净收益', field: 'qOpincome' },
  { headerName: '价值变动单季度净收益', field: 'qInvestincome' },
  { headerName: '扣除非经常损益后的单季度净利润', field: 'qDtprofit' },
  { headerName: '每股收益(单季度)', field: 'qEps' },
  { headerName: '销售净利率(单季度)', field: 'qNetprofitMargin' },
  { headerName: '销售毛利率(单季度)', field: 'qGsprofitMargin' },
  { headerName: '销售期间费用率(单季度)', field: 'qExpToSales' },
  { headerName: '净利润／营业总收入(单季度)', field: 'qProfitToGr' },
  { headerName: '销售费用／营业总收入 (单季度)', field: 'qSaleexpToGr' },
  { headerName: '管理费用／营业总收入 (单季度)', field: 'qAdminexpToGr' },
  { headerName: '财务费用／营业总收入 (单季度)', field: 'qFinaexpToGr' },
  { headerName: '资产减值损失／营业总收入(单季度)', field: 'qImpairToGrTtm' },
  { headerName: '营业总成本／营业总收入 (单季度)', field: 'qGcToGr' },
  { headerName: '营业利润／营业总收入(单季度)', field: 'qOpToGr' },
  { headerName: '净资产收益率(单季度)', field: 'qRoe' },
  { headerName: '净资产单季度收益率(扣除非经常损益)', field: 'qDtRoe' },
  { headerName: '总资产净利润(单季度)', field: 'qNpta' },
  { headerName: '经营活动净收益／利润总额(单季度)', field: 'qOpincomeToEbt' },
  { headerName: '价值变动净收益／利润总额(单季度)', field: 'qInvestincomeToEbt' },
  { headerName: '扣除非经常损益后的净利润／净利润(单季度)', field: 'qDtprofitToProfit' },
  { headerName: '销售商品提供劳务收到的现金／营业收入(单季度)', field: 'qSalescashToOr' },
  { headerName: '经营活动产生的现金流量净额／营业收入(单季度)', field: 'qOcfToSales' },
  { headerName: '经营活动产生的现金流量净额／经营活动净收益(单季度)', field: 'qOcfToOr' },
  { headerName: '基本每股收益同比增长率(%)', field: 'basicEpsYoy' },
  { headerName: '稀释每股收益同比增长率(%)', field: 'dtEpsYoy' },
  { headerName: '每股经营活动产生的现金流量净额同比增长率(%)', field: 'cfpsYoy' },
  { headerName: '营业利润同比增长率(%)', field: 'opYoy' },
  { headerName: '利润总额同比增长率(%)', field: 'ebtYoy' },
  { headerName: '归属母公司股东的净利润同比增长率(%)', field: 'netprofitYoy' },
  { headerName: '归属母公司股东的净利润-扣除非经常损益同比增长率(%)', field: 'dtNetprofitYoy' },
  { headerName: '经营活动产生的现金流量净额同比增长率(%)', field: 'ocfYoy' },
  { headerName: '净资产收益率(摊薄)同比增长率(%)', field: 'roeYoy' },
  { headerName: '每股净资产相对年初增长率(%)', field: 'bpsYoy' },
  { headerName: '资产总计相对年初增长率(%)', field: 'assetsYoy' },
  { headerName: '归属母公司的股东权益相对年初增长率(%)', field: 'eqtYoy' },
  { headerName: '营业总收入同比增长率(%)', field: 'trYoy' },
  { headerName: '营业收入同比增长率(%)', field: 'orYoy' },
  { headerName: '营业总收入同比增长率(%)(单季度)', field: 'qGrYoy' },
  { headerName: '营业总收入环比增长率(%)(单季度)', field: 'qGrQoq' },
  { headerName: '营业收入同比增长率(%)(单季度)', field: 'qSalesYoy' },
  { headerName: '营业收入环比增长率(%)(单季度)', field: 'qSalesQoq' },
  { headerName: '营业利润同比增长率(%)(单季度)', field: 'qOpYoy' },
  { headerName: '营业利润环比增长率(%)(单季度)', field: 'qOpQoq' },
  { headerName: '净利润同比增长率(%)(单季度)', field: 'qProfitYoy' },
  { headerName: '净利润环比增长率(%)(单季度)', field: 'qProfitQoq' },
  { headerName: '归属母公司股东的净利润同比增长率(%)(单季度)', field: 'qNetprofitYoy' },
  { headerName: '归属母公司股东的净利润环比增长率(%)(单季度)', field: 'qNetprofitQoq' },
  { headerName: '净资产同比增长率', field: 'equityYoy' },
  { headerName: '研发费用', field: 'rdExp' },

].map(o => ({
  ...o,
  width: 120,
  filter: 'agNumberColumnFilter', // 显式指定数字过滤
  filterParams: {
    buttons: ['reset', 'apply'], // 增加重置和应用按钮
    closeOnApply: true,
  },
}))

const defaultColDef: ColDef = {
  resizable: true,
  sortable: true,
  // 设置背景色防止文字重叠，设置 flex 基础占比
  cellStyle: { display: 'flex', alignItems: 'center', backgroundColor: 'white' },
}

const columnDefs: ColDef[] = [
  {
    headerName: '序号',
    field: 'index',
    width: 60,
    valueGetter: 'node.rowIndex + 1',
    filter: false,
    sortable: false,
    resizable: false,
  },
  ...annualMetricColumns,
  {
    headerName: '一级行业',
    field: 'l1Name',
    width: 180,
    valueFormatter: params =>
      params.value ? `${params.value} (${params.data?.l1Code})` : '',
    cellClassRules,
    // 关键：定义过滤器搜索的数据范围
    filterValueGetter: (params) => {
      const name = params.data?.l1Name || ''
      const code = params.data?.l1Code || ''
      // 返回一个包含名称和代码的合并字符串，这样过滤器就能同时匹配两者
      return `${name} ${code}`
    },

    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
      // 建议：设为 true，这样用户输入 "801" 就能匹配到包含该代码的行业
      // filterOptions: ['contains', 'notContains', 'equals'],
      debounceMs: 500,
    },
  },
  {
    headerName: '二级行业',
    field: 'l2Name',
    width: 180,
    valueFormatter: params =>
      params.value ? `${params.value} (${params.data?.l2Code})` : '',
    cellClassRules,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '三级行业',
    field: 'l3Name',
    width: 200,
    valueFormatter: params =>
      params.value ? `${params.value} (${params.data?.l3Code})` : '',
    cellClassRules,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '股票名称',
    field: 'name',
    width: 120,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
    // flex: 1,
    cellRenderer: (params: any) => {
      const div = document.createElement('div')
      div.style.cursor = 'pointer' // 鼠标样式
      div.style.color = '#1890ff' // 可选：蓝色表示可点击
      div.textContent = params.value

      div.addEventListener('click', () => {
        // 跳转到详情页，比如用 Vue Router
        router.push(`/stock/${encodeURIComponent(params.data.tsCode)}`)
      })

      return div
    },
  },
  {
    headerName: '股票代码',
    field: 'tsCode',
    width: 120,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '备注',
    field: 'remark',
    width: 200,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '标签',
    field: 'tags',
    width: 150,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    valueFormatter: (params: any) => {
      if (Array.isArray(params.value)) {
        return params.value.join(', ')
      }
      return ''
    },
  },
  ...finaIndicatorColumns,
  {
    headerName: '公司全称',
    field: 'comName',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '公司介绍',
    field: 'introduction',
    width: 300,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '主要业务及产品',
    field: 'mainBusiness',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '统一社会信用代码',
    field: 'comId',
    width: 180,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '交易所',
    field: 'exchange',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '法人代表',
    field: 'chairman',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '总经理',
    field: 'manager',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '董秘',
    field: 'secretary',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '注册资本(万元)',
    field: 'regCapital',
    width: 130,
    filter: 'agNumberColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '注册日期',
    field: 'setupDate',
    width: 120,
    filter: 'agDateColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '所在省份',
    field: 'province',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '所在城市',
    field: 'city',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '公司主页',
    field: 'website',
    width: 160,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    cellRenderer: (params: any) =>
      params.value
        ? `<a href="${
          params.value.startsWith('http') ? params.value : `https://${params.value}`
        }" target="_blank">${params.value}</a>`
        : '',
  },
  {
    headerName: '电子邮件',
    field: 'email',
    width: 160,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '办公室',
    field: 'office',
    width: 200,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '员工人数',
    field: 'employees',
    width: 100,
    filter: 'agNumberColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '主要业务及产品',
    field: 'mainBusiness',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '经营范围',
    field: 'businessScope',
    width: 300,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
    cellClass: 'text-ellipsis', // 添加类名
  },
]
</script>

<template>
  <div class="industry-grid-wrapper h-full">
    <AgGridVue
      class="ag-theme-alpine"
      style="width: 100%; height: 100%"
      :column-defs="columnDefs"
      :row-data="data"
      :default-col-def="defaultColDef"
      :suppress-row-transform="true"
      :animate-rows="true"
      :enable-cell-text-selection="true"
      :ensure-dom-order="true"
      @grid-ready="onGridReady"
      @filter-changed="onFilterChanged"
    />
  </div>
</template>

<style scoped>
/* 关键：将重复的行业文字设为透明，视觉上实现合并效果 */
:deep(.cell-span-hidden) {
  color: transparent !important;
  /* 移除重复单元格的下边框，让这一组看起来像在一个大框里 */
  border-bottom: none !important;
}

/* 优化表格线条 */
.ag-theme-alpine {
  --ag-border-color: #e2e2e2;
}

:deep(.ag-cell) {
  border-right: 1px solid #eee !important;
}

:deep(.annual-bar-grid-cell) {
  padding: 4px 10px !important;
}

:deep(.annual-bar-cell) {
  position: relative;
  display: grid;
  grid-template-columns: repeat(10, minmax(5px, 1fr));
  align-items: stretch;
  gap: 3px;
  width: 100%;
  height: 34px;
}

:deep(.annual-bar-latest) {
  position: absolute;
  top: -1px;
  right: 0;
  z-index: 1;
  max-width: 96px;
  overflow: hidden;
  padding-left: 4px;
  background: rgba(255, 255, 255, 0.85);
  color: #111827;
  font-size: 11px;
  line-height: 13px;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.annual-bar-slot) {
  position: relative;
  min-width: 0;
  height: 100%;
}

:deep(.annual-bar) {
  position: absolute;
  left: 0;
  right: 0;
  bottom: auto;
  border-radius: 2px 2px 0 0;
}

:deep(.annual-bar-placeholder) {
  top: calc(50% - 1px) !important;
  height: 2px !important;
  border-radius: 999px;
  background: #d1d5db !important;
}

.industry-grid-wrapper {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}
</style>
