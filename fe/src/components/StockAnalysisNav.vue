<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  tscode: string
}>()

interface NavItem {
  key: string
  label: string
  desc: string
  icon: string
  accent: string
  route: (tscode: string) => string
}

const items: NavItem[] = [
  {
    key: 'hub',
    label: '工作台',
    desc: '总览与入口',
    icon: '01',
    accent: '#0f766e',
    route: tscode => `/stock/${encodeURIComponent(tscode)}`,
  },
  {
    key: 'card',
    label: '财务卡片',
    desc: '11+ 图表',
    icon: '02',
    accent: '#2563eb',
    route: tscode => `/stock/${encodeURIComponent(tscode)}/card`,
  },
  {
    key: 'cashflow',
    label: '现金流',
    desc: '6 张图',
    icon: '03',
    accent: '#059669',
    route: tscode => `/stock/${encodeURIComponent(tscode)}/cashflow`,
  },
  {
    key: 'income',
    label: '利润表',
    desc: '5 张图',
    icon: '04',
    accent: '#0284c7',
    route: tscode => `/stock/${encodeURIComponent(tscode)}/income`,
  },
  {
    key: 'balance',
    label: '资产负债表',
    desc: '5 张图',
    icon: '05',
    accent: '#b45309',
    route: tscode => `/stock/${encodeURIComponent(tscode)}/balance`,
  },
  {
    key: 'ai-valuation',
    label: 'AI 估值',
    desc: '报告生成',
    icon: '06',
    accent: '#7c3aed',
    route: tscode => `/stock/${encodeURIComponent(tscode)}/ai-valuation`,
  },
]

const navItems = computed(() =>
  items.map(item => ({
    ...item,
    to: item.route(props.tscode),
  })),
)
</script>

<template>
  <nav class="analysis-nav" aria-label="个股分析导航">
    <router-link
      v-for="item in navItems"
      :key="item.key"
      :to="item.to"
      class="nav-card"
      :style="{ '--accent': item.accent }"
    >
      <span class="nav-icon">{{ item.icon }}</span>
      <span class="nav-copy">
        <strong>{{ item.label }}</strong>
        <small>{{ item.desc }}</small>
      </span>
    </router-link>
  </nav>
</template>

<style scoped lang="scss">
.analysis-nav {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.nav-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 78px;
  padding: 14px 16px;
  color: #102a43;
  text-decoration: none;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(241, 245, 249, 0.92)),
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 20%, white), white);
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #dbe4ee);
  border-radius: 18px;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
    border-color: color-mix(in srgb, var(--accent) 36%, #bfdbfe);
  }

  &.router-link-active {
    color: white;
    background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 70%, #0f172a));
    border-color: transparent;
    box-shadow: 0 20px 38px color-mix(in srgb, var(--accent) 24%, rgba(15, 23, 42, 0.28));
  }

  &.router-link-active .nav-icon {
    background: rgba(255, 255, 255, 0.16);
    color: white;
  }

  &.router-link-active small {
    color: rgba(255, 255, 255, 0.76);
  }
}

.nav-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, white);
  border-radius: 14px;
}

.nav-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;

  strong {
    font-size: 15px;
    line-height: 1.15;
  }

  small {
    font-size: 12px;
    color: #52606d;
    line-height: 1.2;
  }
}

@media (max-width: 1200px) {
  .analysis-nav {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .analysis-nav {
    grid-template-columns: 1fr;
  }

  .nav-card {
    min-height: 72px;
    padding: 12px 14px;
  }
}
</style>
