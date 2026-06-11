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
    title: { text: '资产结构', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 亿` },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { top: 40, bottom: 80, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '固定资产', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.fixedAssets)), itemStyle: { color: '#2c91d8' } },
      { name: '金融资产', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.financialAssets)), itemStyle: { color: '#36b37e' } },
      { name: '应收款', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.receivables)), itemStyle: { color: '#ffc400' } },
      { name: '存货', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.inventories)), itemStyle: { color: '#ff4d55' } },
      { name: '商誉', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.goodwill)), itemStyle: { color: '#db35a6' } },
      { name: '无形资产', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.intangibleAssets)), itemStyle: { color: '#6b62e9' } },
      { name: '其他', type: 'bar', stack: 'asset', data: data.map(d => toBillion(d.otherAssets)), itemStyle: { color: '#7b8794' } },
    ],
  } as EChartsOption)
  charts.push(chart1)

  const chart2 = echarts.init(els[1])
  chart2.setOption({
    title: { text: '负债结构', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 亿` },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { top: 40, bottom: 80, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '有息负债', type: 'bar', stack: 'liab', data: data.map(d => toBillion(d.interestBearingDebt)), itemStyle: { color: '#ff4d55' } },
      { name: '应付款', type: 'bar', stack: 'liab', data: data.map(d => toBillion(d.payables)), itemStyle: { color: '#2c91d8' } },
      { name: '合同负债', type: 'bar', stack: 'liab', data: data.map(d => toBillion(d.contractLiabilities)), itemStyle: { color: '#36b37e' } },
      { name: '员工/税', type: 'bar', stack: 'liab', data: data.map(d => toBillion(d.employeeTaxPayables)), itemStyle: { color: '#ffc400' } },
      { name: '其他负债', type: 'bar', stack: 'liab', data: data.map(d => toBillion(d.otherLiabilities)), itemStyle: { color: '#7b8794' } },
    ],
  } as EChartsOption)
  charts.push(chart2)

  const chart3 = echarts.init(els[2])
  const leverageData = data.map((d) => {
    if (d.totalLiab != null && d.totalAssets && d.totalAssets !== 0)
      return +((d.totalLiab / d.totalAssets) * 100).toFixed(1)
    return null
  })
  const interestDebtRatio = data.map((d) => {
    if (d.interestBearingDebt != null && d.totalAssets && d.totalAssets !== 0)
      return +((d.interestBearingDebt / d.totalAssets) * 100).toFixed(1)
    return null
  })
  chart3.setOption({
    title: { text: '杠杆率趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      { name: '资产负债率', type: 'line', data: leverageData, lineStyle: { width: 2.5 }, itemStyle: { color: '#ff4d55' }, markLine: { data: [{ yAxis: 60, label: { formatter: '60%' } }], lineStyle: { color: '#999', type: 'dashed' } } },
      { name: '有息负债/总资产', type: 'line', data: interestDebtRatio, lineStyle: { width: 2.5 }, itemStyle: { color: '#6b62e9' } },
    ],
  } as EChartsOption)
  charts.push(chart3)

  const chart4 = echarts.init(els[3])
  chart4.setOption({
    title: { text: '货币资金 vs 有息负债', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 亿` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '亿元' },
    series: [
      { name: '货币资金', type: 'bar', data: data.map(d => toBillion(d.moneyCap)), itemStyle: { color: '#36b37e' } },
      { name: '有息负债', type: 'bar', data: data.map(d => toBillion(d.interestBearingDebt)), itemStyle: { color: '#ff4d55' } },
      {
        name: '净现金',
        type: 'line',
        data: data.map((d) => {
          if (d.moneyCap != null && d.interestBearingDebt != null)
            return toBillion(d.moneyCap - d.interestBearingDebt)
          return null
        }),
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color: '#2c91d8' },
      },
    ],
  } as EChartsOption)
  charts.push(chart4)

  const chart5 = echarts.init(els[4])
  const goodwillRatio = data.map((d) => {
    if (d.goodwill != null && d.parentEquity && d.parentEquity !== 0)
      return +((d.goodwill / d.parentEquity) * 100).toFixed(1)
    return null
  })
  const receivablesGrowth = data.map((d, i) => {
    const prev = data[i - 1]
    if (i === 0 || !d.receivables || !prev || !prev.receivables) return null
    return +(((d.receivables - prev.receivables) / Math.abs(prev.receivables)) * 100).toFixed(1)
  })
  const revenueGrowth = data.map((d, i) => {
    const prev = data[i - 1]
    if (i === 0 || !d.revenue || !prev || !prev.revenue) return null
    return +(((d.revenue - prev.revenue) / Math.abs(prev.revenue)) * 100).toFixed(1)
  })
  chart5.setOption({
    title: { text: '资产质量风险指标', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v}%` },
    legend: { bottom: 0 },
    grid: { top: 40, bottom: 60, left: 60, right: 20 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%' },
    series: [
      { name: '商誉/净资产', type: 'line', data: goodwillRatio, lineStyle: { width: 2.5 }, itemStyle: { color: '#db35a6' }, markLine: { data: [{ yAxis: 20, label: { formatter: '20% 警戒线' } }], lineStyle: { color: '#ff4d55', type: 'dashed' } } },
      { name: '应收增速', type: 'line', data: receivablesGrowth, lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#ffc400' } },
      { name: '营收增速', type: 'line', data: revenueGrowth, lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#2c91d8' } },
    ],
  } as EChartsOption)
  charts.push(chart5)
}
</script>

<template>
  <div class="balance-analysis">
    <section class="page-hero">
      <div>
        <p class="eyebrow">Balance Sheet</p>
        <h1>资产负债表分析 · {{ stockName }}</h1>
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
        <li><strong>资产结构：</strong>关注固定资产占比（重资产 vs 轻资产）、应收/存货是否异常增长、商誉占比是否过高。</li>
        <li><strong>负债结构：</strong>有息负债（借钱）vs 经营性负债（应付账款、合同负债）。经营性负债多说明对上下游有议价权。</li>
        <li><strong>杠杆率：</strong>资产负债率 < 60% 一般安全（金融/地产除外）。有息负债/总资产关注实际付息压力。</li>
        <li><strong>货币资金 vs 有息负债：</strong>净现金为正说明公司不缺钱。货币资金远低于有息负债需警惕偿债风险。</li>
        <li><strong>资产质量风险：</strong>商誉/净资产 > 20% 有减值风险。应收增速持续高于营收增速说明回款变差。</li>
      </ul>
    </div>
  </div>
</template>

<style scoped lang="scss">
.balance-analysis {
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
    radial-gradient(circle at top right, rgba(251, 191, 36, 0.18), transparent 30%),
    linear-gradient(135deg, #1f2937 0%, #92400e 54%, #b45309 100%);
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
  .balance-analysis {
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
