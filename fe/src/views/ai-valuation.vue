<script setup lang="ts">
import type { FinanceCardResponse } from '@/api/finance'
import { computed, ref, watch } from 'vue'
import StockAnalysisNav from '@/components/StockAnalysisNav.vue'
import { getFinanceCard } from '@/api/finance'
import { generateValuation, saveValuation } from '@/api/ai'

const props = defineProps<{ tscode: string }>()

const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const cardData = ref<FinanceCardResponse | null>(null)
const analysisContent = ref('')
const modelUsed = ref('')
const generatedAt = ref('')
const savedPath = ref('')
const error = ref('')

const stockName = computed(() => cardData.value?.stock?.name || props.tscode)
const summaryLine = computed(() =>
  [
    props.tscode,
    cardData.value?.industry?.l3Name || cardData.value?.stock?.industry || '',
    cardData.value?.financeSeries.length ? `近 ${Math.min(cardData.value.financeSeries.length, 5)} 期财务样本` : '',
  ].filter(Boolean).join(' · '),
)

const latestPoint = computed(() => cardData.value?.financeSeries.at(-1) ?? null)
const summaryStats = computed(() => [
  {
    label: '收盘价',
    value: formatDecimal(latestPoint.value?.close, 2),
  },
  {
    label: 'PE(TTM)',
    value: formatDecimal(latestPoint.value?.pe, 1),
  },
  {
    label: 'PB',
    value: formatDecimal(latestPoint.value?.pb, 2),
  },
  {
    label: '最新财报期',
    value: latestPoint.value?.period || '--',
  },
])

const renderedMarkdown = computed(() => renderMarkdown(analysisContent.value))

watch(
  () => props.tscode,
  async () => {
    analysisContent.value = ''
    modelUsed.value = ''
    generatedAt.value = ''
    savedPath.value = ''
    error.value = ''
    await loadData()
  },
  { immediate: true },
)

async function loadData() {
  loading.value = true
  try {
    const res = await getFinanceCard(props.tscode, 5)
    cardData.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  generating.value = true
  error.value = ''
  savedPath.value = ''
  try {
    const res = await generateValuation(props.tscode)
    analysisContent.value = res.data.analysis
    modelUsed.value = res.data.model_used
    generatedAt.value = res.data.generated_at
  } catch (e: any) {
    error.value = e?.response?.data?.msg || e?.message || '生成失败，请检查 AI 配置'
  } finally {
    generating.value = false
  }
}

async function handleSave() {
  if (!analysisContent.value) return
  saving.value = true
  error.value = ''
  try {
    const res = await saveValuation(props.tscode, analysisContent.value)
    savedPath.value = res.data.path
  } catch (e: any) {
    error.value = e?.response?.data?.msg || e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function formatDecimal(value: number | null | undefined, digits: number) {
  if (value == null || Number.isNaN(value))
    return '--'
  return value.toFixed(digits)
}

function renderMarkdown(text: string): string {
  if (!text.trim())
    return ''

  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inList = false

  const pushParagraph = (content: string) => {
    if (!content.trim()) return
    html.push(`<p>${renderInline(content)}</p>`)
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()

    if (!line) {
      if (inList) {
        html.push('</ul>')
        inList = false
      }
      continue
    }

    if (/^###\s+/.test(line)) {
      if (inList) {
        html.push('</ul>')
        inList = false
      }
      html.push(`<h3>${renderInline(line.replace(/^###\s+/, ''))}</h3>`)
      continue
    }

    if (/^##\s+/.test(line)) {
      if (inList) {
        html.push('</ul>')
        inList = false
      }
      html.push(`<h2>${renderInline(line.replace(/^##\s+/, ''))}</h2>`)
      continue
    }

    if (/^#\s+/.test(line)) {
      if (inList) {
        html.push('</ul>')
        inList = false
      }
      html.push(`<h1>${renderInline(line.replace(/^#\s+/, ''))}</h1>`)
      continue
    }

    if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        html.push('<ul>')
        inList = true
      }
      html.push(`<li>${renderInline(line.replace(/^[-*]\s+/, ''))}</li>`)
      continue
    }

    if (inList) {
      html.push('</ul>')
      inList = false
    }
    pushParagraph(line)
  }

  if (inList)
    html.push('</ul>')

  return html.join('')
}

function renderInline(text: string) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
</script>

<template>
  <div class="ai-valuation">
    <section class="page-hero">
      <div>
        <p class="eyebrow">AI Valuation</p>
        <h1>AI 估值卡片 · {{ stockName }}</h1>
        <p class="summary">{{ summaryLine }}</p>
      </div>
      <div class="hero-stats">
        <div
          v-for="stat in summaryStats"
          :key="stat.label"
          class="hero-stat"
        >
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
        </div>
      </div>
    </section>

    <StockAnalysisNav :tscode="tscode" />

    <div v-if="loading" class="loading">加载基础数据中...</div>

    <div v-else class="content">
      <div class="action-bar">
        <button
          class="btn-generate"
          :disabled="generating"
          @click="handleGenerate"
        >
          {{ generating ? '分析中...' : '生成 AI 估值分析' }}
        </button>
        <button
          v-if="analysisContent"
          class="btn-save"
          :disabled="saving"
          @click="handleSave"
        >
          {{ saving ? '保存中...' : '保存为 MD 文件' }}
        </button>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="savedPath" class="success-msg">已保存至：{{ savedPath }}</div>

      <div v-if="generating" class="generating">
        <div class="spinner" />
        <p>正在调用 AI 分析，请稍候（可能需要 30-60 秒）...</p>
      </div>

      <div v-if="analysisContent && !generating" class="analysis-card">
        <div class="card-header">
          <span class="model-tag">{{ modelUsed }}</span>
          <span class="time-tag">{{ generatedAt }}</span>
        </div>
        <div class="card-body markdown-body" v-html="renderedMarkdown" />
      </div>

      <div v-if="!analysisContent && !generating && !error" class="empty-state">
        <p>点击上方按钮，AI 将基于该股票近 5 年财务数据生成估值分析报告。</p>
        <p class="hint">需要在后端 .env 中配置 AI_API_URL 和 AI_API_KEY。</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.ai-valuation {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.9fr);
  gap: 22px;
  margin-bottom: 18px;
  padding: 24px 26px;
  color: white;
  background:
    radial-gradient(circle at top right, rgba(192, 132, 252, 0.22), transparent 30%),
    linear-gradient(135deg, #111827 0%, #312e81 54%, #7c3aed 100%);
  border-radius: 24px;
  box-shadow: 0 24px 50px rgba(49, 46, 129, 0.18);

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

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.hero-stat {
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;

  span {
    display: block;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.72);
  }

  strong {
    display: block;
    margin-top: 10px;
    font-size: 22px;
    line-height: 1.1;
  }
}

.loading {
  text-align: center;
  padding: 60px;
  color: #52606d;
}

.content {
  margin-top: 18px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-generate,
.btn-save {
  padding: 11px 22px;
  color: white;
  border: none;
  border-radius: 999px;
  font-size: 14px;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    opacity 0.18s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-generate {
  background: linear-gradient(135deg, #312e81, #7c3aed);
}

.btn-save {
  background: linear-gradient(135deg, #047857, #10b981);
}

.error-msg,
.success-msg {
  padding: 12px 16px;
  border-radius: 14px;
  margin-bottom: 16px;
  font-size: 13px;
}

.error-msg {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
}

.success-msg {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #389e0d;
}

.generating {
  text-align: center;
  padding: 48px 20px;
  color: #52606d;

  p {
    margin-top: 16px;
  }
}

.spinner {
  width: 34px;
  height: 34px;
  border: 3px solid #e5e7eb;
  border-top-color: #7c3aed;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.analysis-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  overflow: hidden;
  background: white;
}

.card-header {
  padding: 14px 16px;
  background: linear-gradient(180deg, #faf5ff, #f8fafc);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.model-tag {
  padding: 4px 10px;
  background: #ede9fe;
  border: 1px solid #c4b5fd;
  border-radius: 999px;
  font-size: 12px;
  color: #5b21b6;
}

.time-tag {
  font-size: 12px;
  color: #64748b;
}

.card-body {
  padding: 24px;
  font-size: 14px;
  line-height: 1.9;

  :deep(h1) {
    margin: 0 0 10px;
    font-size: 22px;
    color: #111827;
  }

  :deep(h2) {
    margin: 20px 0 8px;
    font-size: 18px;
    color: #1f2937;
  }

  :deep(h3) {
    margin: 18px 0 8px;
    font-size: 15px;
    color: #334155;
  }

  :deep(p) {
    margin: 0 0 12px;
    color: #334155;
  }

  :deep(ul) {
    margin: 0 0 12px;
    padding-left: 20px;
  }

  :deep(li) {
    margin-bottom: 6px;
    color: #334155;
  }

  :deep(code) {
    padding: 1px 6px;
    background: #f3f4f6;
    border-radius: 6px;
    font-size: 13px;
  }
}

.empty-state {
  text-align: center;
  padding: 64px 20px;
  color: #52606d;

  p {
    margin: 8px 0;
  }
}

.hint {
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 900px) {
  .ai-valuation {
    padding: 16px;
  }

  .page-hero {
    grid-template-columns: 1fr;
    padding: 20px;
  }

  .hero-stats {
    grid-template-columns: 1fr 1fr;
  }

  .content {
    padding: 18px;
  }
}

@media (max-width: 640px) {
  .hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
