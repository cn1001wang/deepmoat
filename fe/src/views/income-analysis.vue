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

const toBillion = (v: number | null) => v != null ? +(v / 1e8).toFixed(2) : null

const filteredSeries = computed(() => {
  if (!cardData.value) return []
  const series = cardData.value.financeSeries
  if (showAllPeriods.value) return series
  return series.filter(p => p.period.endsWith('1231'))
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
    title: { text: '营收与净利润趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 60 },
    xAxis: { type: 'category', data: labels },
    yAxis: [
      { type: 'value', name: '亿元' },
      { type: 'value', name: '增速%', axisLabel: { formatter: '{value}%' }, splitLine: { show: false } },
    ],
    series: [
      { name: '营收', type: 'bar', data: data.map(d => toBillion(d.revenue)), itemStyle: { color: '#2c91d8' } },
      { name: '净利润', type: 'bar', data: data.map(d => toBillion(d.netProfit)), itemStyle: { color: '#36b37e' } },
      {
        name: '营收YoY',
        type: 'line',
        yAxisIndex: 1,
        data: data.map((d, i) => {
          const prev = data[i - 1]
          if (i === 0 || !d.revenue || !prev || !prev.revenue) return null
          return +(((d.revenue - prev.revenue) / Math.abs(prev.revenue)) * 100).toFixed(1)
        }),
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color: '#6b62e9' },
      },
    ],
  } as EChartsOption)
  charts.push(chart1)

  const chart2 = echarts.init(els[1])
  chart2.setOption({
    title: { text: '毛利率与净利率趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%', axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '毛利率', type: 'line', data: data.map(d => d.grossMargin != null ? +(d.grossMargin * 100).toFixed(2) : null), lineStyle: { width: 2.5 }, itemStyle: { color: '#2c91d8' }, areaStyle: { opacity: 0.05 } },
      { name: '净利率', type: 'line', data: data.map(d => d.netProfitMargin != null ? +(d.netProfitMargin * 100).toFixed(2) : null), lineStyle: { width: 2.5 }, itemStyle: { color: '#ff4d55' }, areaStyle: { opacity: 0.05 } },
    ],
  } as EChartsOption)
  charts.push(chart2)

  const chart3 = echarts.init(els[2])
  chart3.setOption({
    title: { text: '费用率分解', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      { name: '销售费用率', type: 'bar', stack: 'expense', data: data.map(d => d.salesExpenseRatio != null ? +(d.salesExpenseRatio * 100).toFixed(2) : null), itemStyle: { color: '#ff4d55' } },
      { name: '管理费用率', type: 'bar', stack: 'expense', data: data.map(d => d.adminExpenseRatio != null ? +(d.adminExpenseRatio * 100).toFixed(2) : null), itemStyle: { color: '#ffc400' } },
      { name: '财务费用率', type: 'bar', stack: 'expense', data: data.map(d => d.financeExpenseRatio != null ? +(d.financeExpenseRatio * 100).toFixed(2) : null), itemStyle: { color: '#15b8c8' } },
      { name: '研发费用率', type: 'bar', stack: 'expense', data: data.map(d => d.rdExpenseRatio != null ? +(d.rdExpenseRatio * 100).toFixed(2) : null), itemStyle: { color: '#6b62e9' } },
    ],
  } as EChartsOption)
  charts.push(chart3)

  const chart4 = echarts.init(els[3])
  chart4.setOption({
    title: { text: '利润质量：主营利润 vs 其他收益', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '主营业务利润', type: 'bar', stack: 'profit', data: data.map(d => toBillion(d.mainBusinessProfit)), itemStyle: { color: '#2c91d8' } },
      { name: '投资收益', type: 'bar', stack: 'profit', data: data.map(d => toBillion(d.investIncome)), itemStyle: { color: '#ffc400' } },
      { name: '营业外净额', type: 'bar', stack: 'profit', data: data.map(d => toBillion(d.nonOperatingBalance)), itemStyle: { color: '#7b8794' } },
      { name: '其他收益', type: 'bar', stack: 'profit', data: data.map(d => toBillion(d.otherIncome)), itemStyle: { color: '#15b8c8' } },
    ],
  } as EChartsOption)
  charts.push(chart4)

  const chart5 = echarts.init(els[4])
  chart5.setOption({
    title: { text: 'ROE 趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    grid: { top: 40, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      {
        name: 'ROE',
        type: 'line',
        data: data.map(d => d.roe != null ? +(d.roe * 100).toFixed(2) : null),
        lineStyle: { width: 3 },
        itemStyle: { color: '#6b62e9' },
        areaStyle: { opacity: 0.08 },
        markLine: { data: [{ yAxis: 15, label: { formatter: '15%' } }], lineStyle: { color: '#36b37e', type: 'dashed' } },
      },
    ],
  } as EChartsOption)
  charts.push(chart5)
}
</script>

<template>
  <div class="income-analysis">
    <section class="page-hero">
      <div>
        <p class="eyebrow">Income Statement</p>
        <h1>利润表分析 · {{ stockName }}</h1>
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
      <div ref="chartRefs" class="chart-box" />
      <div ref="chartRefs" class="chart-box" />
      <div ref="chartRefs" class="chart-box" />
      <div ref="chartRefs" class="chart-box" />
      <div ref="chartRefs" class="chart-box wide" />
    </div>

    <div v-if="cardData && filteredSeries.length" class="reading-guide">
      <h3>阅读指南</h3>
      <ul>
        <li><strong>营收与净利润：</strong>关注增速是否匹配，净利润增速持续低于营收增速说明利润率在压缩。</li>
        <li><strong>毛利率/净利率：</strong>稳定或上升趋势是竞争优势的体现，持续下降需警惕价格战或成本压力。</li>
        <li><strong>费用率：</strong>销售费用率高说明品牌力弱需要推广；管理费用率高说明管理效率低；研发费用率高可能是护城河投入。</li>
        <li><strong>利润质量：</strong>主营利润占比越高越好。投资收益、营业外收入占比高说明利润不可持续。</li>
        <li><strong>ROE：</strong>长期稳定在 15% 以上是优质公司的标志。关注 ROE 是靠利润率、周转率还是杠杆驱动。</li>
      </ul>
    </div>
  </div>
</template>

<style scoped lang="scss">
.income-analysis {
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
    radial-gradient(circle at top right, rgba(96, 165, 250, 0.22), transparent 30%),
    linear-gradient(135deg, #102a43 0%, #0f4c81 54%, #0284c7 100%);
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

  &.wide {
    grid-column: span 2;
  }
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
  .income-analysis {
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

  .chart-box.wide {
    grid-column: span 1;
  }
}
</style>
