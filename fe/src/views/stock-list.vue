<!--  -->
<script setup lang="ts">
import type { FinaIndicator, Stock, IndustryTreeNode, DailyBasic } from '@/api/finance'
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import { getIndexMember, getStockBasicAll, getStockCompany, getSWIndustry, getFinaIndicator, buildIndustryTree, getDailyBasic } from '@/api/finance'
import StockListTable from '@/components/StockListTable.vue'
import { toFixed } from '@/utils'
import IndustryTree from '@/components/IndustryTree.vue'

const stockList = ref<Stock[]>([])
const industryTree = ref<IndustryTreeNode[]>([])
/**
 * 对股票列表进行多级排序：
 * 1. l1Code (升序)
 * 2. l2Code (升序)
 * 3. l3Code (升序)
 * 4. tsCode (升序)
 */
function sortStockList(stocks: Stock[]): Stock[] {
  return [...stocks].sort((a, b) => {
    // 1. 比较 l1Code
    const res1 = (a.l1Code || '').localeCompare(b.l1Code || '')
    if (res1 !== 0)
      return res1

    // 2. l1Code 相同时，比较 l2Code
    const res2 = (a.l2Code || '').localeCompare(b.l2Code || '')
    if (res2 !== 0)
      return res2

    // 3. l2Code 相同时，比较 l3Code
    const res3 = (a.l3Code || '').localeCompare(b.l3Code || '')
    if (res3 !== 0)
      return res3

    // 4. 全部相同时，按 tsCode 排序
    return (a.tsCode || '').localeCompare(b.tsCode || '')
  })
}
/**
 * @param {boolean} disclosed - true: 确定已披露, false: 最近一期
 * @param {Date} d - 基准日期
 */
const getPeriod = (disclosed = false, d = new Date()) => {
  const y = d.getFullYear(), m = d.getMonth() + 1, md = m * 100 + d.getDate();

  if (disclosed) {
    // 确定披露模式：依据 4.30, 8.31, 10.31 三个法定节点
    if (md < 430) return `${y - 1}0930`;
    return `${y}${md < 831 ? '0331' : md < 1031 ? '0630' : '0930'}`;
  }

  // 最近一期模式：只要季度结束就跳转
  return m < 4 ? `${y - 1}1231` : `${y}${m < 7 ? '0331' : m < 10 ? '0630' : '0930'}`;
};
const endDate = getPeriod(true) // 示例公告日期

/**
 * 获取最近一个交易日
 * 逻辑：
 * 1. 如果今天是工作日且时间 > 15:00，则交易日为今天
 * 2. 否则，从昨天开始向前找，直到找到第一个周一至周五
 */
function getLatestTradingDay(): Date {
  const now = new Date();
  const currentDay = now.getDay(); // 0 是周日，6 是周六
  const currentHour = now.getHours();

  // 1. 初始化检查点
  let targetDate = new Date(now);

  // 判断今天是否已经是“已收盘的交易日”
  const isWorkday = currentDay !== 0 && currentDay !== 6;
  const isAfterMarketClose = currentHour >= 15;

  if (!(isWorkday && isAfterMarketClose)) {
    // 如果今天不是工作日，或者还没到3点，则从昨天开始向前找
    targetDate.setDate(targetDate.getDate() - 1);
  }

  // 2. 循环回溯，直到跳过所有周末
  // getDay(): 0 (周日), 6 (周六)
  while (targetDate.getDay() === 0 || targetDate.getDay() === 6) {
    targetDate.setDate(targetDate.getDate() - 1);
  }

  // 重置时间为 00:00:00，方便后续对比（可选）
  targetDate.setHours(0, 0, 0, 0);

  return targetDate;
}

// --- 测试代码 ---
const tradingDay = dayjs(getLatestTradingDay()).format('YYYYMMDD');
const pick = <T, K extends keyof T>(o: T, k: K[]) => k.reduce((r, c) => (r[c] = o[c], r), {} as Pick<T, K>);
function loadData() {
  Promise.all([getSWIndustry(), getStockBasicAll(), getIndexMember(), getStockCompany(),getFinaIndicator({endDate}), getDailyBasic({tradeDate: tradingDay})]).then((res) => {
    const [{ data: industry }, { data: stock }, { data: member }, { data: company }, { data: finaIndicator }, {data: dailyBasic}] = res
    industryTree.value = buildIndustryTree(industry)
    const _stockList: Stock[] = []
    stock.forEach((item) => {
      const indexMember = member.find(o => o.tsCode === item.tsCode)
      let finaIndicatorItem: FinaIndicator = finaIndicator.find(o => o.tsCode === item.tsCode) || {} as FinaIndicator
      let dailyBasicItem: DailyBasic  = dailyBasic.find(o => o.tsCode === item.tsCode) || {} as DailyBasic
      // pick(finaIndicatorItem, ['roe'])
      dailyBasicItem.totalMv = dailyBasicItem.totalMv?toFixed(dailyBasicItem.totalMv/10000,2):0 // 转换为亿元单位
      _stockList.push({
        ...item,
        ...company.find(o => o.tsCode === item.tsCode),
        ...indexMember,
        ...finaIndicatorItem,
        ...dailyBasicItem,
      })
    })

    // 按照一级行业排序

    stockList.value = sortStockList(_stockList)
  })
}
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="p-28px h-full">
    <!-- <div class="h-120px overflow-auto mb-14px">
    <IndustryTree :data="industryTree"/>
    </div> -->
    <div class="h-full">
      <StockListTable :data="stockList" />
    </div>
  </div>
</template>

<style lang='scss' scoped>

</style>
