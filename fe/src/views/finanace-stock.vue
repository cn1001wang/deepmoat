<script setup lang="ts">
import type { FinanceCardPoint, FinanceCardResponse } from '@/api/finance'
import { computed, ref, watch } from 'vue'
import TsCodeTable from '@/components/TsCodeTable.vue'
import StockAnalysisNav from '@/components/StockAnalysisNav.vue'
import { getFinanceCard } from '@/api/finance'

const props = defineProps<{ tscode: string }>()

const loading = ref(false)
const error = ref('')
const cardData = ref<FinanceCardResponse | null>(null)

interface AnalysisEntry {
  key: string
  title: string
  subtitle: string
  route: string
  accent: string
  count: string
  highlights: string[]
}

const analysisEntries = computed<AnalysisEntry[]>(() => [
  {
    key: 'card',
    title: '财务卡片',
    subtitle: '从估值、盈利、资产结构到主营构成的一页式总览',
    route: `/stock/${encodeURIComponent(props.tscode)}/card`,
    accent: '#2563eb',
    count: '11+ 图表',
    highlights: ['估值与周期位置', '盈利能力', '资产与资本结构'],
  },
  {
    key: 'cashflow',
    title: '现金流质量',
    subtitle: '把 OCF、FCF、收现比和资本开支放到一张图谱里看清楚',
    route: `/stock/${encodeURIComponent(props.tscode)}/cashflow`,
    accent: '#059669',
    count: '6 张图',
    highlights: ['OCF vs 净利润', 'FCF 走势', '收现比'],
  },
  {
    key: 'income',
    title: '利润表分析',
    subtitle: '看收入、利润率、费用率和 ROE 背后的经营趋势',
    route: `/stock/${encodeURIComponent(props.tscode)}/income`,
    accent: '#0284c7',
    count: '5 张图',
    highlights: ['营收净利趋势', '费用率拆解', '利润质量'],
  },
  {
    key: 'balance',
    title: '资产负债表',
    subtitle: '识别轻重资产、杠杆水平、偿债能力和资产质量风险',
    route: `/stock/${encodeURIComponent(props.tscode)}/balance`,
    accent: '#c2410c',
    count: '5 张图',
    highlights: ['资产结构', '负债结构', '现金覆盖债务'],
  },
  {
    key: 'ai-valuation',
    title: 'AI 估值卡片',
    subtitle: '调用外部 LLM 生成可保存的 Markdown 估值分析草稿',
    route: `/stock/${encodeURIComponent(props.tscode)}/ai-valuation`,
    accent: '#7c3aed',
    count: 'Markdown',
    highlights: ['自动生成分析', '支持保存为 .md', '适合二次编辑'],
  },
])

const sortedSeries = computed(() => [...(cardData.value?.financeSeries ?? [])])
const latestPoint = computed(() => sortedSeries.value.at(-1) ?? null)
const latestAnnualPoint = computed(() => {
  const annual = [...sortedSeries.value].reverse().find(point => point.period.endsWith('1231'))
  return annual ?? latestPoint.value
})

const stockName = computed(() => cardData.value?.stock?.name || props.tscode)
const stockMeta = computed(() =>
  [
    props.tscode,
    cardData.value?.industry?.l3Name || cardData.value?.stock?.industry || '',
    cardData.value?.stock?.area || '',
    cardData.value?.stock?.market || '',
  ].filter(Boolean).join(' · '),
)

const heroStats = computed(() => [
  {
    label: latestPoint.value?.valuationDate ? `收盘价(${latestPoint.value.valuationDate})` : '收盘价',
    value: formatDecimal(latestPoint.value?.close, 2, '--'),
  },
  {
    label: 'PE(TTM)',
    value: formatDecimal(latestPoint.value?.pe, 1, '--'),
  },
  {
    label: 'PB',
    value: formatDecimal(latestPoint.value?.pb, 2, '--'),
  },
  {
    label: '最新财报期',
    value: latestPoint.value?.period || '--',
  },
])

const snapshotCards = computed(() => [
  {
    label: latestAnnualPoint.value?.period ? `${latestAnnualPoint.value.period.slice(0, 4)} 营收` : '营收',
    value: formatBillion(latestAnnualPoint.value?.revenue),
    tone: '#2563eb',
  },
  {
    label: latestAnnualPoint.value?.period ? `${latestAnnualPoint.value.period.slice(0, 4)} 归母净利` : '归母净利',
    value: formatBillion(latestAnnualPoint.value?.netProfit),
    tone: '#059669',
  },
  {
    label: 'ROE',
    value: formatPercent(latestAnnualPoint.value?.roe),
    tone: '#7c3aed',
  },
  {
    label: '经营现金流',
    value: formatBillion(latestAnnualPoint.value?.operatingCashFlow),
    tone: '#0284c7',
  },
  {
    label: '资产负债率',
    value: formatPercent(calcLeverage(latestAnnualPoint.value)),
    tone: '#c2410c',
  },
  {
    label: '现金/有息债务',
    value: formatRatio(calcCashDebtCoverage(latestAnnualPoint.value)),
    tone: '#0f766e',
  },
])

const missingModules = computed(() => cardData.value?.missingModules ?? [])

watch(
  () => props.tscode,
  async () => {
    await loadData()
  },
  { immediate: true },
)

async function loadData() {
  loading.value = true
  error.value = ''
  cardData.value = null
  try {
    const res = await getFinanceCard(props.tscode, 10)
    cardData.value = res.data
  } catch (err: any) {
    error.value = err?.response?.data?.msg || err?.message || '加载个股分析页失败'
  } finally {
    loading.value = false
  }
}

function calcLeverage(point: FinanceCardPoint | null) {
  if (!point?.totalAssets || point.totalLiab == null)
    return null
  if (point.totalAssets === 0)
    return null
  return point.totalLiab / point.totalAssets
}

function calcCashDebtCoverage(point: FinanceCardPoint | null) {
  if (!point?.interestBearingDebt || point.moneyCap == null)
    return null
  if (point.interestBearingDebt === 0)
    return null
  return point.moneyCap / point.interestBearingDebt
}

function formatBillion(value: number | null | undefined) {
  if (value == null)
    return '--'
  return `${(value / 1e8).toFixed(1)} 亿`
}

function formatDecimal(value: number | null | undefined, digits = 2, fallback = '--') {
  if (value == null || Number.isNaN(value))
    return fallback
  return value.toFixed(digits)
}

function formatPercent(value: number | null | undefined) {
  if (value == null)
    return '--'
  return `${(value * 100).toFixed(1)}%`
}

function formatRatio(value: number | null | undefined) {
  if (value == null)
    return '--'
  return `${value.toFixed(2)}x`
}
</script>

<template>
  <div class="stock-workspace">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Stock Workspace</p>
        <h1>{{ stockName }}</h1>
        <p class="hero-meta">{{ stockMeta }}</p>
        <p class="hero-desc">
          从这里进入财务卡片、三表分析和 AI 估值。下方保留原始财务指标表，方便在图表和明细之间来回切换。
        </p>
      </div>
      <div class="hero-stats">
        <div
          v-for="stat in heroStats"
          :key="stat.label"
          class="hero-stat"
        >
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
        </div>
      </div>
    </section>

    <StockAnalysisNav :tscode="tscode" />

    <div v-if="loading" class="state-card">正在加载个股工作台...</div>
    <div v-else-if="error" class="state-card state-error">{{ error }}</div>

    <template v-else>
      <section class="snapshot-grid">
        <article
          v-for="card in snapshotCards"
          :key="card.label"
          class="snapshot-card"
          :style="{ '--tone': card.tone }"
        >
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="entry-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">入口导航</p>
            <h2>围绕一只股票的 5 个分析页面</h2>
          </div>
          <p class="section-copy">
            当前入口页会把图表页和指标表放在一起，适合先扫一眼，再按问题深入。
          </p>
        </div>

        <div class="entry-grid">
          <router-link
            v-for="entry in analysisEntries"
            :key="entry.key"
            :to="entry.route"
            class="entry-card"
            :style="{ '--accent': entry.accent }"
          >
            <div class="entry-top">
              <div>
                <p class="entry-count">{{ entry.count }}</p>
                <h3>{{ entry.title }}</h3>
              </div>
              <span class="entry-arrow">→</span>
            </div>
            <p class="entry-subtitle">{{ entry.subtitle }}</p>
            <ul class="entry-highlights">
              <li v-for="highlight in entry.highlights" :key="highlight">{{ highlight }}</li>
            </ul>
          </router-link>
        </div>
      </section>

      <section v-if="missingModules.length" class="notice-panel">
        <p class="section-kicker">数据提醒</p>
        <h2>当前有部分模块缺失</h2>
        <p>这些页面仍可访问，但部分图表可能出现空值。缺失标识: {{ missingModules.join('、') }}</p>
      </section>

      <section class="table-panel">
        <div class="section-heading">
          <div>
            <p class="section-kicker">原始明细</p>
            <h2>财务指标表</h2>
          </div>
          <p class="section-copy">
            保留查询、备注与标签功能，方便把图形化结论回落到具体财务项目。
          </p>
        </div>
        <TsCodeTable :tscode="tscode" />
      </section>
    </template>
  </div>
</template>

<style scoped lang="scss">
.stock-workspace {
  min-height: 100vh;
  padding: 28px 24px 40px;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.16), transparent 24%),
    radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 22%),
    linear-gradient(180deg, #f7fafc 0%, #eef4f8 100%);
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 1fr);
  gap: 24px;
  margin-bottom: 20px;
  padding: 28px;
  color: white;
  background:
    radial-gradient(circle at top right, rgba(45, 212, 191, 0.24), transparent 30%),
    linear-gradient(135deg, #102a43 0%, #0f4c81 58%, #136f8a 100%);
  border-radius: 28px;
  box-shadow: 0 28px 60px rgba(16, 42, 67, 0.22);
}

.eyebrow,
.section-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy {
  h1 {
    margin: 0;
    font-size: clamp(32px, 4vw, 44px);
    line-height: 1.05;
  }
}

.hero-meta {
  margin: 12px 0 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.78);
}

.hero-desc {
  max-width: 760px;
  margin: 18px 0 0;
  font-size: 15px;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.88);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.hero-stat {
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  backdrop-filter: blur(14px);

  span {
    display: block;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.72);
  }

  strong {
    display: block;
    margin-top: 10px;
    font-size: 24px;
    line-height: 1.1;
  }
}

.state-card,
.notice-panel,
.table-panel,
.entry-section {
  margin-top: 22px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 24px;
  box-shadow: 0 22px 45px rgba(15, 23, 42, 0.06);
}

.state-error {
  color: #b42318;
  background: #fff4f2;
  border-color: #fecdca;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
  margin-top: 22px;
}

.snapshot-card {
  padding: 18px;
  background: white;
  border: 1px solid color-mix(in srgb, var(--tone) 16%, #dbe4ee);
  border-radius: 18px;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);

  span {
    display: block;
    font-size: 12px;
    color: #52606d;
  }

  strong {
    display: block;
    margin-top: 12px;
    font-size: 24px;
    line-height: 1.1;
    color: var(--tone);
  }
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;

  h2 {
    margin: 0;
    font-size: 26px;
    color: #102a43;
  }
}

.section-copy {
  max-width: 520px;
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #52606d;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.entry-card {
  display: block;
  padding: 20px;
  text-decoration: none;
  color: #102a43;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92)),
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 16%, white), white);
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #dbe4ee);
  border-radius: 20px;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 32px rgba(15, 23, 42, 0.08);
  }
}

.entry-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;

  h3 {
    margin: 6px 0 0;
    font-size: 22px;
    color: #102a43;
  }
}

.entry-count {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}

.entry-arrow {
  font-size: 24px;
  color: var(--accent);
}

.entry-subtitle {
  margin: 14px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: #52606d;
}

.entry-highlights {
  margin: 16px 0 0;
  padding-left: 18px;
  color: #334e68;

  li {
    margin-bottom: 8px;
    line-height: 1.5;
  }
}

.notice-panel {
  p {
    margin: 10px 0 0;
    line-height: 1.7;
    color: #52606d;
  }

  h2 {
    margin: 0;
    font-size: 24px;
    color: #102a43;
  }
}

@media (max-width: 1180px) {
  .hero-panel {
    grid-template-columns: 1fr;
  }

  .snapshot-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .stock-workspace {
    padding: 18px 14px 28px;
  }

  .hero-panel,
  .state-card,
  .notice-panel,
  .table-panel,
  .entry-section {
    padding: 18px;
    border-radius: 20px;
  }

  .hero-stats,
  .snapshot-grid,
  .entry-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
    align-items: start;
  }
}
</style>
