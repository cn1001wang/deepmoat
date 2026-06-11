<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStockBasicAll } from '@/api/finance'

const router = useRouter()
const stockCount = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getStockBasicAll()
    stockCount.value = res.data.length
  } catch {}
  loading.value = false
})

const features = [
  {
    title: '股票筛选器',
    desc: '排雷 + 4种策略模板 + 100分评分',
    icon: '🔍',
    route: '/screener',
    color: '#2c91d8',
  },
  {
    title: '股票列表',
    desc: '全市场股票浏览与行业分类',
    icon: '📋',
    route: '/StockList',
    color: '#36b37e',
  },
  {
    title: '行业分类',
    desc: '申万三级行业树形浏览',
    icon: '🏢',
    route: '/Industry',
    color: '#6b62e9',
  },
]

const analysisTools = [
  { title: '财务卡片', desc: '11+图表全方位财务可视化', route: '/stock/{code}/card', icon: '📊', color: '#15b8c8' },
  { title: '现金流质量', desc: '经营现金流、FCF、收现比', route: '/stock/{code}/cashflow', icon: '💰', color: '#36b37e' },
  { title: '利润表分析', desc: '营收增速、利润率、费用率', route: '/stock/{code}/income', icon: '📈', color: '#2c91d8' },
  { title: '资产负债表', desc: '资产结构、杠杆率、偿债能力', route: '/stock/{code}/balance', icon: '🏦', color: '#ffc400' },
  { title: 'AI 估值分析', desc: 'AI 生成深度估值报告并保存', route: '/stock/{code}/ai-valuation', icon: '🤖', color: '#6b62e9' },
  { title: '财务指标表', desc: '6年核心指标对比表格', route: '/stock/{code}', icon: '📑', color: '#7b8794' },
]

const quickStocks = [
  { code: '600519.SH', name: '贵州茅台' },
  { code: '000858.SZ', name: '五粮液' },
  { code: '002714.SZ', name: '牧原股份' },
  { code: '601012.SH', name: '隆基绿能' },
  { code: '000001.SZ', name: '平安银行' },
  { code: '600036.SH', name: '招商银行' },
]
</script>

<template>
  <div class="home">
    <header class="hero">
      <div class="hero-content">
        <h1 class="title">DeepMoat</h1>
        <p class="subtitle">知价值之本，行投资之真</p>
        <p class="desc">基于巴菲特+芒格投资体系的 A 股深度分析平台</p>
        <div v-if="!loading" class="stats">
          <div class="stat-item">
            <span class="stat-num">{{ stockCount.toLocaleString() }}</span>
            <span class="stat-label">覆盖股票</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">5</span>
            <span class="stat-label">分析维度</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">4</span>
            <span class="stat-label">筛选策略</span>
          </div>
        </div>
      </div>
    </header>

    <section class="section">
      <h2 class="section-title">快速入口</h2>
      <div class="feature-grid">
        <router-link
          v-for="f in features"
          :key="f.route"
          :to="f.route"
          class="feature-card"
          :style="{ '--accent': f.color }"
        >
          <span class="feature-icon">{{ f.icon }}</span>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </router-link>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">个股分析工具</h2>
      <p class="section-hint">选择一只股票先进入个股工作台，再切到具体分析页</p>
      <div class="quick-stocks">
        <span
          v-for="s in quickStocks"
          :key="s.code"
          class="stock-chip"
          @click="router.push(`/stock/${s.code}`)"
        >
          {{ s.name }}
        </span>
      </div>
      <div class="tools-grid">
        <div
          v-for="t in analysisTools"
          :key="t.title"
          class="tool-card"
          :style="{ '--accent': t.color }"
        >
          <span class="tool-icon">{{ t.icon }}</span>
          <div class="tool-info">
            <h4>{{ t.title }}</h4>
            <p>{{ t.desc }}</p>
          </div>
          <div class="tool-actions">
            <router-link
              v-for="s in quickStocks.slice(0, 3)"
              :key="s.code"
              :to="t.route.replace('{code}', s.code)"
              class="tool-link"
            >
              {{ s.name }}
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <section class="section workflow-section">
      <h2 class="section-title">投资工作流</h2>
      <div class="workflow">
        <div class="workflow-step">
          <div class="step-num">1</div>
          <h4>排雷</h4>
          <p>剔除 ST、审计异常、连续亏损</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-num">2</div>
          <h4>筛选</h4>
          <p>策略模板 + 参数化筛选</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-num">3</div>
          <h4>分析</h4>
          <p>三表分析 + 现金流质量</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-num">4</div>
          <h4>估值</h4>
          <p>AI 估值 + 安全边际判断</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-num">5</div>
          <h4>跟踪</h4>
          <p>观察池管理 + 指标监控</p>
        </div>
      </div>
      <div class="workflow-cta">
        <router-link to="/screener" class="cta-btn">从筛选开始</router-link>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.home {
  min-height: 100vh;
  background: #f8f9fa;
}

.hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 80px 40px 60px;
  text-align: center;
  color: white;
}
.hero-content {
  max-width: 700px;
  margin: 0 auto;
}
.title {
  font-size: 48px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #e2e8f0, #ffffff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle {
  font-size: 20px;
  margin: 12px 0 8px;
  color: #94a3b8;
  font-weight: 300;
}
.desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-top: 40px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-num {
  font-size: 32px;
  font-weight: 700;
  color: #38bdf8;
}
.stat-label {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
}
.section-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #1e293b;
}
.section-hint {
  font-size: 13px;
  color: #94a3b8;
  margin: 0 0 20px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 24px;
}
.feature-card {
  display: flex;
  flex-direction: column;
  padding: 28px 24px;
  background: white;
  border-radius: 12px;
  text-decoration: none;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    border-color: var(--accent);
  }
  .feature-icon { font-size: 32px; margin-bottom: 12px; }
  h3 { font-size: 16px; margin: 0 0 8px; }
  p { font-size: 13px; color: #64748b; margin: 0; }
}

.quick-stocks {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.stock-chip {
  padding: 6px 14px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  &:hover {
    background: #2c91d8;
    color: white;
    border-color: #2c91d8;
  }
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.tool-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 20px;
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
  &:hover { border-color: var(--accent); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .tool-icon { font-size: 28px; flex-shrink: 0; margin-top: 2px; }
  .tool-info {
    flex: 1;
    h4 { margin: 0 0 4px; font-size: 14px; color: #1e293b; }
    p { margin: 0; font-size: 12px; color: #94a3b8; }
  }
  .tool-actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .tool-link {
    font-size: 11px;
    color: #2c91d8;
    text-decoration: none;
    padding: 2px 8px;
    border-radius: 4px;
    background: #f0f7ff;
    &:hover { background: #2c91d8; color: white; }
  }
}

.workflow-section {
  background: white;
  border-radius: 16px;
  margin: 0 auto 48px;
  max-width: 1200px;
  border: 1px solid #e2e8f0;
}
.workflow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
  flex-wrap: wrap;
}
.workflow-step {
  text-align: center;
  padding: 20px 24px;
  border-radius: 10px;
  background: #f8fafc;
  min-width: 130px;
  .step-num {
    width: 28px;
    height: 28px;
    line-height: 28px;
    border-radius: 50%;
    background: #2c91d8;
    color: white;
    font-size: 13px;
    font-weight: 600;
    margin: 0 auto 10px;
  }
  h4 { margin: 0 0 4px; font-size: 14px; }
  p { margin: 0; font-size: 11px; color: #94a3b8; }
}
.workflow-arrow {
  font-size: 20px;
  color: #cbd5e1;
}
.workflow-cta {
  text-align: center;
  margin-top: 32px;
}
.cta-btn {
  display: inline-block;
  padding: 12px 32px;
  background: linear-gradient(135deg, #2c91d8, #6b62e9);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.2s;
  &:hover { opacity: 0.9; }
}
</style>
