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
  { title: '资产负债表', desc: '资产结构、杠杆率、偿债能力', route: '/stock/{code}/balance', icon: '🏦', color: '#b45309' },
  { title: 'AI 估值分析', desc: 'AI 生成深度估值报告并保存', route: '/stock/{code}/ai-valuation', icon: '🤖', color: '#7c3aed' },
  { title: '财务指标表', desc: '6年核心指标对比表格', route: '/stock/{code}', icon: '📑', color: '#0f766e' },
]

const quickStocks = [
  { code: '600519.SH', name: '贵州茅台' },
  { code: '000858.SZ', name: '五粮液' },
  { code: '002714.SZ', name: '牧原股份' },
  { code: '601012.SH', name: '隆基绿能' },
  { code: '000001.SZ', name: '平安银行' },
  { code: '600036.SH', name: '招商银行' },
]

function setElementStyle(event: MouseEvent, styles: Partial<CSSStyleDeclaration>) {
  const target = event.currentTarget as HTMLElement | null
  if (target)
    Object.assign(target.style, styles)
}
</script>

<template>
  <div class="home" style="min-height: 100vh; background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); padding: 40px 32px;">
    <div style="max-width: 1400px; margin: 0 auto;">
      <header class="hero" style="margin-bottom: 64px; text-align: center;">
        <div class="hero-content">
          <h1 class="title" style="font-size: 56px; margin: 0 0 12px 0; font-weight: 900; letter-spacing: -0.03em; background: linear-gradient(135deg, #0f172a 0%, #334155 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">DeepMoat</h1>
          <p class="subtitle" style="font-size: 22px; margin: 0 0 10px 0; color: #475569; font-weight: 300;">知价值之本，行投资之真</p>
          <p class="desc" style="font-size: 16px; margin: 0 0 32px 0; color: #64748b;">基于巴菲特+芒格投资体系的 A 股深度分析平台</p>
          <div v-if="!loading" class="stats" style="display: flex; justify-content: center; gap: 64px;">
            <div class="stat-item" style="text-align: center;">
              <span class="stat-num" style="display: block; font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">{{ stockCount.toLocaleString() }}</span>
              <span class="stat-label" style="font-size: 14px; color: #64748b;">覆盖股票</span>
            </div>
            <div class="stat-item" style="text-align: center;">
              <span class="stat-num" style="display: block; font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">5</span>
              <span class="stat-label" style="font-size: 14px; color: #64748b;">分析维度</span>
            </div>
            <div class="stat-item" style="text-align: center;">
              <span class="stat-num" style="display: block; font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">4</span>
              <span class="stat-label" style="font-size: 14px; color: #64748b;">筛选策略</span>
            </div>
          </div>
        </div>
      </header>

      <section class="section" style="margin-bottom: 64px;">
        <h2 class="section-title" style="font-size: 28px; margin: 0 0 24px 0; color: #0f172a; font-weight: 700;">快速入口</h2>
        <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px;">
          <router-link
            v-for="f in features"
            :key="f.route"
            :to="f.route"
            class="feature-card"
            :style="{ '--accent': f.color }"
            style="
              display: flex;
              align-items: center;
              gap: 20px;
              padding: 32px;
              text-decoration: none;
              color: #0f172a;
              background: white;
              border: 1px solid color-mix(in srgb, var(--accent) 16%, #e2e8f0);
              border-radius: 22px;
              box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
              transition: all 0.2s ease;
            "
            @mouseover="e => setElementStyle(e, { transform: 'translateY(-3px)' })"
            @mouseout="e => setElementStyle(e, { transform: 'translateY(0)' })"
          >
            <span class="feature-icon" style="
              display: grid;
              place-items: center;
              width: 64px;
              height: 64px;
              font-size: 28px;
              background: color-mix(in srgb, var(--accent) 10%, white);
              border-radius: 20px;
            ">{{ f.icon }}</span>
            <div style="flex: 1;">
              <h3 style="font-size: 20px; margin: 0 0 6px 0; font-weight: 700;">{{ f.title }}</h3>
              <p style="font-size: 14px; margin: 0; color: #475569;">{{ f.desc }}</p>
            </div>
          </router-link>
        </div>
      </section>

      <section class="section" style="margin-bottom: 64px;">
        <h2 class="section-title" style="font-size: 28px; margin: 0 0 12px 0; color: #0f172a; font-weight: 700;">个股分析工具</h2>
        <p class="section-hint" style="font-size: 14px; margin: 0 0 24px 0; color: #64748b;">选择一只股票先进入个股工作台，再切到具体分析页</p>
        <div class="quick-stocks" style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 32px;">
          <span
            v-for="s in quickStocks"
            :key="s.code"
            class="stock-chip"
            style="
              padding: 10px 20px;
              background: white;
              border: 1px solid #cbd5e1;
              border-radius: 12px;
              font-size: 14px;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.15s ease;
            "
            @click="router.push(`/stock/${s.code}`)"
            @mouseover="e => setElementStyle(e, { borderColor: '#2563eb', color: '#2563eb' })"
            @mouseout="e => setElementStyle(e, { borderColor: '#cbd5e1', color: '#0f172a' })"
          >
            {{ s.name }}
          </span>
        </div>
        <div class="tools-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px;">
          <div
            v-for="t in analysisTools"
            :key="t.title"
            class="tool-card"
            :style="{ '--accent': t.color }"
            style="
              padding: 24px;
              background: white;
              border: 1px solid color-mix(in srgb, var(--accent) 14%, #e2e8f0);
              border-radius: 18px;
              box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
              transition: all 0.2s ease;
            "
            @mouseover="e => setElementStyle(e, { transform: 'translateY(-2px)' })"
            @mouseout="e => setElementStyle(e, { transform: 'translateY(0)' })"
          >
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
              <span class="tool-icon" style="
                display: grid;
                place-items: center;
                width: 48px;
                height: 48px;
                font-size: 24px;
                background: color-mix(in srgb, var(--accent) 10%, white);
                border-radius: 14px;
              ">{{ t.icon }}</span>
              <div class="tool-info" style="flex: 1;">
                <h4 style="font-size: 18px; margin: 0 0 4px 0; font-weight: 700;">{{ t.title }}</h4>
                <p style="font-size: 13px; margin: 0; color: #475569;">{{ t.desc }}</p>
              </div>
            </div>
            <div class="tool-actions" style="display: flex; gap: 10px; flex-wrap: wrap;">
              <router-link
                v-for="s in quickStocks.slice(0, 3)"
                :key="s.code"
                :to="t.route.replace('{code}', s.code)"
                class="tool-link"
                style="
                  padding: 8px 14px;
                  font-size: 13px;
                  font-weight: 500;
                  color: var(--accent);
                  background: color-mix(in srgb, var(--accent) 10%, white);
                  border-radius: 10px;
                  text-decoration: none;
                  transition: all 0.15s ease;
                "
                @mouseover="e => setElementStyle(e, { background: 'var(--accent)', color: 'white' })"
                @mouseout="e => setElementStyle(e, { background: 'color-mix(in srgb, var(--accent) 10%, white)', color: 'var(--accent)' })"
              >
                {{ s.name }}
              </router-link>
            </div>
          </div>
        </div>
      </section>

      <section class="section workflow-section">
        <h2 class="section-title" style="font-size: 28px; margin: 0 0 24px 0; color: #0f172a; font-weight: 700; text-align: center;">投资工作流</h2>
        <div class="workflow" style="display: flex; align-items: center; justify-content: center; gap: 16px; flex-wrap: wrap; margin-bottom: 32px;">
          <div class="workflow-step" style="
            flex: 0 0 160px;
            padding: 24px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            text-align: center;
          ">
            <div class="step-num" style="
              width: 40px;
              height: 40px;
              margin: 0 auto 12px auto;
              display: grid;
              place-items: center;
              background: linear-gradient(135deg, #2563eb, #7c3aed);
              color: white;
              font-size: 18px;
              font-weight: 700;
              border-radius: 50%;
            ">1</div>
            <h4 style="font-size: 16px; margin: 0 0 6px 0; font-weight: 700;">排雷</h4>
            <p style="font-size: 13px; margin: 0; color: #475569;">剔除 ST、审计异常、连续亏损</p>
          </div>
          <div class="workflow-arrow" style="font-size: 24px; color: #94a3b8; font-weight: 700;">→</div>
          <div class="workflow-step" style="
            flex: 0 0 160px;
            padding: 24px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            text-align: center;
          ">
            <div class="step-num" style="
              width: 40px;
              height: 40px;
              margin: 0 auto 12px auto;
              display: grid;
              place-items: center;
              background: linear-gradient(135deg, #059669, #10b981);
              color: white;
              font-size: 18px;
              font-weight: 700;
              border-radius: 50%;
            ">2</div>
            <h4 style="font-size: 16px; margin: 0 0 6px 0; font-weight: 700;">筛选</h4>
            <p style="font-size: 13px; margin: 0; color: #475569;">策略模板 + 参数化筛选</p>
          </div>
          <div class="workflow-arrow" style="font-size: 24px; color: #94a3b8; font-weight: 700;">→</div>
          <div class="workflow-step" style="
            flex: 0 0 160px;
            padding: 24px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            text-align: center;
          ">
            <div class="step-num" style="
              width: 40px;
              height: 40px;
              margin: 0 auto 12px auto;
              display: grid;
              place-items: center;
              background: linear-gradient(135deg, #0284c7, #0ea5e9);
              color: white;
              font-size: 18px;
              font-weight: 700;
              border-radius: 50%;
            ">3</div>
            <h4 style="font-size: 16px; margin: 0 0 6px 0; font-weight: 700;">分析</h4>
            <p style="font-size: 13px; margin: 0; color: #475569;">三表分析 + 现金流质量</p>
          </div>
          <div class="workflow-arrow" style="font-size: 24px; color: #94a3b8; font-weight: 700;">→</div>
          <div class="workflow-step" style="
            flex: 0 0 160px;
            padding: 24px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            text-align: center;
          ">
            <div class="step-num" style="
              width: 40px;
              height: 40px;
              margin: 0 auto 12px auto;
              display: grid;
              place-items: center;
              background: linear-gradient(135deg, #b45309, #f59e0b);
              color: white;
              font-size: 18px;
              font-weight: 700;
              border-radius: 50%;
            ">4</div>
            <h4 style="font-size: 16px; margin: 0 0 6px 0; font-weight: 700;">估值</h4>
            <p style="font-size: 13px; margin: 0; color: #475569;">AI 估值 + 安全边际判断</p>
          </div>
          <div class="workflow-arrow" style="font-size: 24px; color: #94a3b8; font-weight: 700;">→</div>
          <div class="workflow-step" style="
            flex: 0 0 160px;
            padding: 24px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            text-align: center;
          ">
            <div class="step-num" style="
              width: 40px;
              height: 40px;
              margin: 0 auto 12px auto;
              display: grid;
              place-items: center;
              background: linear-gradient(135deg, #7c3aed, #a78bfa);
              color: white;
              font-size: 18px;
              font-weight: 700;
              border-radius: 50%;
            ">5</div>
            <h4 style="font-size: 16px; margin: 0 0 6px 0; font-weight: 700;">跟踪</h4>
            <p style="font-size: 13px; margin: 0; color: #475569;">观察池管理 + 指标监控</p>
          </div>
        </div>
        <div class="workflow-cta" style="text-align: center;">
          <router-link to="/screener" class="cta-btn" style="
            display: inline-block;
            padding: 14px 32px;
            font-size: 16px;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            border-radius: 14px;
            text-decoration: none;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.24);
            transition: all 0.15s ease;
          " @mouseover="e => setElementStyle(e, { transform: 'translateY(-2px)' })"
            @mouseout="e => setElementStyle(e, { transform: 'translateY(0)' })">
            从筛选开始
          </router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped lang="scss">
/* 响应式适配 */
@media (max-width: 960px) {
  .home {
    padding: 24px 16px !important;
  }

  .hero .title {
    font-size: 42px !important;
  }

  .stats {
    gap: 32px !important;
  }

  .feature-grid {
    grid-template-columns: 1fr !important;
  }

  .tools-grid {
    grid-template-columns: 1fr !important;
  }

  .workflow {
    flex-direction: column;
    gap: 12px !important;
  }

  .workflow-arrow {
    transform: rotate(90deg);
  }
}
</style>
