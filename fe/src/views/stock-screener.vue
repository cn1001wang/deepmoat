<script setup lang="ts">
import type { ScreenerStock, ScreenerMeta, ScreenerParams } from '@/api/screener'
import { ref } from 'vue'
import { runScreener } from '@/api/screener'

const strategies = ['稳健价值型', '高质量成长型', '高股息低估值型', '困境反转型']
const selectedStrategy = ref('稳健价值型')
const loading = ref(false)
const results = ref<ScreenerStock[]>([])
const meta = ref<ScreenerMeta | null>(null)

const params = ref<ScreenerParams>({
  min_roe: 10,
  max_debt_ratio: 60,
  min_cashflow_ratio: 0.8,
})

function onStrategyChange() {
  switch (selectedStrategy.value) {
    case '稳健价值型':
      params.value = { min_roe: 10, max_debt_ratio: 60, min_cashflow_ratio: 0.8, min_dividend_yield: 2 }
      break
    case '高质量成长型':
      params.value = { min_roe: 15, max_debt_ratio: 60, min_cashflow_ratio: 0.8 }
      break
    case '高股息低估值型':
      params.value = { min_dividend_yield: 3, max_debt_ratio: 70 }
      break
    case '困境反转型':
      params.value = { max_debt_ratio: 70 }
      break
  }
}

async function handleRun() {
  loading.value = true
  try {
    const res = await runScreener(selectedStrategy.value, params.value, 5)
    results.value = res.data.stocks
    meta.value = res.data.meta
  } finally {
    loading.value = false
  }
}

function scoreColor(score: number): string {
  if (score >= 80) return '#36b37e'
  if (score >= 65) return '#2c91d8'
  if (score >= 50) return '#ffc400'
  return '#ff4d55'
}

function scoreLabel(score: number): string {
  if (score >= 80) return 'A'
  if (score >= 65) return 'B'
  if (score >= 50) return 'C'
  return 'D'
}
</script>

<template>
  <div class="stock-screener">
    <div class="header">
      <h2>股票筛选器</h2>
    </div>

    <div class="layout">
      <aside class="sidebar">
        <div class="panel">
          <h3>策略选择</h3>
          <select v-model="selectedStrategy" class="strategy-select" @change="onStrategyChange">
            <option v-for="s in strategies" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="panel">
          <h3>参数配置</h3>
          <div class="param-row">
            <label>最低 ROE (%)</label>
            <input v-model.number="params.min_roe" type="number" step="1">
          </div>
          <div class="param-row">
            <label>最高负债率 (%)</label>
            <input v-model.number="params.max_debt_ratio" type="number" step="5">
          </div>
          <div class="param-row">
            <label>最低现金流/利润</label>
            <input v-model.number="params.min_cashflow_ratio" type="number" step="0.1">
          </div>
          <div class="param-row">
            <label>最低股息率 (%)</label>
            <input v-model.number="params.min_dividend_yield" type="number" step="0.5">
          </div>
        </div>

        <button class="btn-run" :disabled="loading" @click="handleRun">
          {{ loading ? '筛选中...' : '开始筛选' }}
        </button>
      </aside>

      <main class="main-content">
        <div v-if="meta" class="meta-bar">
          <span>全市场 <strong>{{ meta.total }}</strong> 只</span>
          <span>排雷剔除 <strong>{{ meta.eliminated }}</strong> 只</span>
          <span>通过筛选 <strong>{{ meta.passed }}</strong> 只</span>
          <span>策略：<strong>{{ meta.strategy }}</strong></span>
        </div>

        <div v-if="loading" class="loading">筛选中，请稍候...</div>

        <table v-else-if="results.length" class="result-table">
          <thead>
            <tr>
              <th>#</th>
              <th>代码</th>
              <th>名称</th>
              <th>行业</th>
              <th>ROE均值</th>
              <th>负债率</th>
              <th>现金流/利润</th>
              <th>评分</th>
              <th>分类</th>
              <th>风险</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stock, idx) in results" :key="stock.tsCode">
              <td>{{ idx + 1 }}</td>
              <td class="code">{{ stock.tsCode }}</td>
              <td>{{ stock.name }}</td>
              <td>{{ stock.industry || '-' }}</td>
              <td>{{ stock.avgRoe }}%</td>
              <td>{{ stock.debtRatio != null ? `${stock.debtRatio}%` : '-' }}</td>
              <td>{{ stock.cashflowRatio != null ? stock.cashflowRatio.toFixed(2) : '-' }}</td>
              <td :style="{ color: scoreColor(stock.score), fontWeight: 'bold' }">{{ stock.score }}</td>
              <td>
                <span class="score-badge" :style="{ background: scoreColor(stock.score) }">
                  {{ scoreLabel(stock.score) }}
                </span>
              </td>
              <td>
                <span v-for="r in stock.risks" :key="r.type" class="risk-tag" :class="r.severity">
                  {{ r.detail }}
                </span>
                <span v-if="!stock.risks.length" class="no-risk">无</span>
              </td>
              <td class="actions">
                <router-link :to="`/stock/${stock.tsCode}/card`">卡片</router-link>
                <router-link :to="`/stock/${stock.tsCode}/cashflow`">现金流</router-link>
                <router-link :to="`/stock/${stock.tsCode}/ai-valuation`">AI估值</router-link>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else-if="!loading && !meta" class="empty-state">
          <p>选择策略和参数后，点击"开始筛选"运行排雷+筛选+评分。</p>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.stock-screener {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}
.header {
  margin-bottom: 20px;
  h2 { margin: 0; font-size: 20px; }
}
.layout {
  display: flex;
  gap: 24px;
}
.sidebar {
  width: 260px;
  flex-shrink: 0;
}
.panel {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  h3 { margin: 0 0 12px; font-size: 14px; color: #333; }
}
.strategy-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}
.param-row {
  margin-bottom: 12px;
  label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; }
  input {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 13px;
  }
}
.btn-run {
  width: 100%;
  padding: 12px;
  background: #2c91d8;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  &:hover:not(:disabled) { background: #1a7bc0; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}
.main-content {
  flex: 1;
  min-width: 0;
}
.meta-bar {
  display: flex;
  gap: 20px;
  padding: 12px 16px;
  background: #f0f7ff;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 13px;
  strong { color: #2c91d8; }
}
.loading { text-align: center; padding: 60px; color: #999; }
.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  th, td { padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; }
  th { background: #fafafa; font-weight: 600; position: sticky; top: 0; }
  tr:hover td { background: #f8f8f8; }
  .code { font-family: monospace; }
}
.score-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: bold;
}
.risk-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  margin-right: 4px;
  &.high { background: #fff2f0; color: #cf1322; border: 1px solid #ffccc7; }
  &.medium { background: #fffbe6; color: #ad6800; border: 1px solid #ffe58f; }
  &.low { background: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }
}
.no-risk { color: #999; font-size: 12px; }
.actions {
  a {
    color: #2c91d8;
    text-decoration: none;
    margin-right: 8px;
    font-size: 12px;
    &:hover { text-decoration: underline; }
  }
}
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
}
</style>
