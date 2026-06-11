import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'
import FinanceStock from '@/views/finanace-stock.vue'
import StockCard from '@/views/stock-card.vue'
import StockList from '@/views/stock-list.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/stock/:tscode',
    name: 'FinanceStock',
    component: FinanceStock,
    props: true,
  },
  {
    path: '/stock/:tscode/card',
    name: 'StockCard',
    component: StockCard,
    props: true,
  },
  {
    path: '/StockList',
    name: 'StockList',
    component: StockList,
  },
  {
    path: '/Industry',
    name: 'Industry',
    component: () => import('@/views/Industry.vue'),
  },
  {
    path: '/screener',
    name: 'StockScreener',
    component: () => import('@/views/stock-screener.vue'),
  },
  {
    path: '/stock/:tscode/cashflow',
    name: 'CashFlowAnalysis',
    component: () => import('@/views/cashflow-analysis.vue'),
    props: true,
  },
  {
    path: '/stock/:tscode/income',
    name: 'IncomeAnalysis',
    component: () => import('@/views/income-analysis.vue'),
    props: true,
  },
  {
    path: '/stock/:tscode/balance',
    name: 'BalanceAnalysis',
    component: () => import('@/views/balance-analysis.vue'),
    props: true,
  },
  {
    path: '/stock/:tscode/ai-valuation',
    name: 'AiValuation',
    component: () => import('@/views/ai-valuation.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
