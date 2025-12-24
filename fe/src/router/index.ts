import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'
import FinanceStock from '@/views/finanace-stock.vue'
import StockList from '@/views/stock-list.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    redirect: '/StockList',
  },
  {
    path: '/stock-detail',
    name: 'FinanceStock',
    component: FinanceStock,
  },
  {
    path: '/StockList',
    name: 'StockList',
    component: StockList,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
