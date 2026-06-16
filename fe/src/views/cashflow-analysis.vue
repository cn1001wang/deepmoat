<script setup lang="ts">
import type { ECharts, EChartsOption } from 'echarts'
import type { FinanceCardResponse } from '@/api/finance'
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import StockAnalysisNav from '@/components/StockAnalysisNav.vue'
import { getFinanceCard } from '@/api/finance'

const props = defineProps<{ tscode: string }>()

const loading = ref(false)
const cardData = ref<FinanceCardResponse | null>(null)
const showAllPeriods = ref(false)
const charts: ECharts[] = []
const chartRefs = ref<HTMLDivElement[]>([])
function setChartRef(el: any, index: number) {
  if (el) chartRefs.value[index] = el as HTMLDivElement
}

const toBillion = (v: number | null) => v != null ? v / 1e8 : null

const filteredSeries = computed(() => {
  if (!cardData.value) return []
  const series = cardData.value.financeSeries
  if (showAllPeriods.value) return series
  return series.filter(p => p.period.endsWith('-12-31'))
})

const periods = computed(() => filteredSeries.value.map(p => p.period.slice(0, 4)))
const stockName = computed(() => cardData.value?.stock?.name || props.tscode)
const summaryLine = computed(() =>
  [
    props.tscode,
    cardData.value?.industry?.l3Name || cardData.value?.stock?.industry || '',
    filteredSeries.value.length ? `${filteredSeries.value.length} 个财报样本` : '',
  ].filter(Boolean).join(' · '),
)

async function loadData() {
  loading.value = true
  try {
    const res = await getFinanceCard(props.tscode, 10)
    cardData.value = res.data
  } finally {
    loading.value = false
  }
}

watch(
  () => props.tscode,
  async () => {
    await loadData()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach(c => c.dispose())
})

window.addEventListener('resize', handleResize)

function handleResize() {
  charts.forEach(c => c.resize())
}

watch(filteredSeries, async () => {
  await nextTick()
  renderCharts()
})

function renderCharts() {
  charts.forEach(c => c.dispose())
  charts.length = 0
  const els = chartRefs.value
  if (!els.length || !filteredSeries.value.length) return

  const data = filteredSeries.value
  const labels = periods.value

  const chart1 = echarts.init(els[0])
  chart1.setOption({
    title: { text: '经营现金流 vs 净利润', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v?.toFixed(2)} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '经营现金流', type: 'bar', data: data.map(d => toBillion(d.operatingCashFlow)), itemStyle: { color: '#2c91d8' } },
      { name: '净利润', type: 'bar', data: data.map(d => toBillion(d.netProfit)), itemStyle: { color: '#ff4d55' } },
    ],
  } as EChartsOption)
  charts.push(chart1)

  const chart2 = echarts.init(els[1])
  chart2.setOption({
    title: { text: '自由现金流趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v?.toFixed(2)} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '维持性FCF', type: 'line', data: data.map(d => toBillion(d.freeCashFlowAfterMaintenance)), lineStyle: { width: 2 }, itemStyle: { color: '#36b37e' } },
      { name: '实际FCF', type: 'line', data: data.map(d => toBillion(d.actualFreeCashFlow)), lineStyle: { width: 2 }, itemStyle: { color: '#6b62e9' } },
    ],
  } as EChartsOption)
  charts.push(chart2)

  const chart3 = echarts.init(els[2])
  const cashRatio = data.map((d) => {
    if (d.operatingCashFlow && d.netProfit && d.netProfit !== 0)
      return +((d.operatingCashFlow / d.netProfit) * 100).toFixed(1)
    return null
  })
  chart3.setOption({
    title: { text: '现金流含金量（经营现金流/净利润）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    grid: { top: 40, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%', axisLabel: { formatter: '{value}%' } },
    series: [
      { name: 'OCF/净利润', type: 'line', data: cashRatio, lineStyle: { width: 2.5 }, itemStyle: { color: '#15b8c8' }, markLine: { data: [{ yAxis: 100, label: { formatter: '100%' } }], lineStyle: { color: '#999', type: 'dashed' } } },
    ],
  } as EChartsOption)
  charts.push(chart3)

  const chart4 = echarts.init(els[3])
  const capexRatio = data.map((d) => {
    if (d.actualCapex && d.operatingCashFlow && d.operatingCashFlow !== 0)
      return +(Math.abs(d.actualCapex) / d.operatingCashFlow * 100).toFixed(1)
    return null
  })
  chart4.setOption({
    title: { text: '资本开支 / 经营现金流', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    grid: { top: 40, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      {
        name: 'Capex/OCF',
        type: 'bar',
        data: capexRatio,
        itemStyle: { color: (params: any) => (params.data > 100 ? '#ff4d55' : params.data > 60 ? '#ffc400' : '#36b37e') },
      },
    ],
    visualMap: { show: false, pieces: [{ lte: 60, color: '#36b37e' }, { gt: 60, lte: 100, color: '#ffc400' }, { gt: 100, color: '#ff4d55' }], dimension: 1 },
  } as EChartsOption)
  charts.push(chart4)

  const chart5 = echarts.init(els[4])
  chart5.setOption({
    title: { text: '三大现金流结构', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v?.toFixed(2)} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '经营活动', type: 'bar', stack: 'total', data: data.map(d => toBillion(d.operatingCashFlow)), itemStyle: { color: '#2c91d8' } },
      {
        name: '投资活动',
        type: 'bar',
        stack: 'total',
        data: data.map((d) => {
          const invest = (d.financialWealthInvestNet || 0) + (d.productionOperationInvestNet || 0) + (d.maInvestNet || 0)
          return toBillion(invest || null)
        }),
        itemStyle: { color: '#ff4d55' },
      },
      {
        name: '筹资活动',
        type: 'bar',
        stack: 'total',
        data: data.map((d) => {
          const finance = (d.equityFinancingNet || 0) + (d.interestDebtFinancingNet || 0) + (d.dividendInterestPaymentNet || 0)
          return toBillion(finance || null)
        }),
        itemStyle: { color: '#ffc400' },
      },
    ],
  } as EChartsOption)
  charts.push(chart5)

  const chart6 = echarts.init(els[5])
  const revCashRatio = data.map((d) => {
    if (d.salesGoodsCash && d.revenue && d.revenue !== 0)
      return +((d.salesGoodsCash / d.revenue) * 100).toFixed(1)
    return null
  })
  chart6.setOption({
    title: { text: '收现比（销售收现/营收）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    grid: { top: 40, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      { name: '收现比', type: 'line', data: revCashRatio, lineStyle: { width: 2.5 }, itemStyle: { color: '#6b62e9' }, areaStyle: { opacity: 0.1 }, markLine: { data: [{ yAxis: 100, label: { formatter: '100%' } }], lineStyle: { color: '#999', type: 'dashed' } } },
    ],
  } as EChartsOption)
  charts.push(chart6)
}
</script>

<template>
  <div class="cashflow-analysis">
    <section class="page-hero">
      <div>
        <p class="eyebrow">Cash Flow</p>
        <h1>现金流质量分析 · {{ stockName }}</h1>
        <p class="summary">{{ summaryLine }}</p>
      </div>
      <div class="controls">
        <label class="toggle">
          <input v-model="showAllPeriods" type="checkbox">
          <span>显示所有季度</span>
        </label>
      </div>
    </section>

    <StockAnalysisNav :tscode="tscode" />

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="charts-grid">
      <div :ref="(el) => setChartRef(el, 0)" class="chart-box" />
      <div :ref="(el) => setChartRef(el, 1)" class="chart-box" />
      <div :ref="(el) => setChartRef(el, 2)" class="chart-box" />
      <div :ref="(el) => setChartRef(el, 3)" class="chart-box" />
      <div :ref="(el) => setChartRef(el, 4)" class="chart-box" />
      <div :ref="(el) => setChartRef(el, 5)" class="chart-box" />
    </div>

    <div v-if="cardData && filteredSeries.length" class="reading-guide">
      <h3>阅读指南</h3>
      <ul>
        <li><strong>经营现金流 vs 净利润：</strong>经营现金流长期高于净利润说明利润含金量高，反之需警惕。</li>
        <li><strong>自由现金流：</strong>维持性 FCF = OCF - 维护性资本开支；实际 FCF = OCF - 全部资本开支。长期为正是好生意的标志。</li>
        <li><strong>现金流含金量：</strong>OCF/净利润 > 100% 为优质，80%-100% 正常，< 60% 需要警惕利润质量。</li>
        <li><strong>资本开支/OCF：</strong>< 60% 正常区间，60%-100% 偏高，> 100% 激进扩张。</li>
        <li><strong>收现比：</strong>销售收到现金/营收 > 100% 说明回款好，< 80% 需关注应收账款风险。</li>
      </ul>
    </div>
  </div>
</template>

<style scoped lang="scss">
.cashflow-analysis {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin-bottom: 18px;
  padding: 24px 26px;
  color: white;
  background:
    radial-gradient(circle at top right, rgba(45, 212, 191, 0.22), transparent 28%),
    linear-gradient(135deg, #0f172a 0%, #0f4c5c 58%, #0f766e 100%);
  border-radius: 24px;

  h1 {
    margin: 0;
    font-size: clamp(28px, 4vw, 36px);
    line-height: 1.08;
  }
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.summary {
  margin: 10px 0 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.toggle {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  font-size: 14px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #52606d;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 18px;
}

.chart-box {
  height: 360px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.06);
}

.reading-guide {
  margin-top: 24px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.05);

  h3 {
    margin: 0 0 12px;
    font-size: 16px;
    color: #102a43;
  }

  ul {
    margin: 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.7;
    color: #334e68;
  }
}

@media (max-width: 900px) {
  .cashflow-analysis {
    padding: 16px;
  }

  .page-hero {
    flex-direction: column;
    align-items: start;
    padding: 20px;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
