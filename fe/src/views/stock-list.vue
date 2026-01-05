<!--  -->
<script setup lang="ts">
import type { FinaIndicator, Stock } from '@/api/finance'
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import { getIndexMember, getStockBasicAll, getStockCompany, getSWIndustry, getFinaIndicator } from '@/api/finance'
import StockListTable from '@/components/StockListTable.vue'

const stockList = ref<Stock[]>([])

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
const pick = <T, K extends keyof T>(o: T, k: K[]) => k.reduce((r, c) => (r[c] = o[c], r), {} as Pick<T, K>);
function loadData() {
  Promise.all([getSWIndustry(), getStockBasicAll(), getIndexMember(), getStockCompany(),getFinaIndicator({endDate} )]).then((res) => {
    const [{ data: industry }, { data: stock }, { data: member }, { data: company }, { data: finaIndicator }] = res
    console.log(finaIndicator)
    const _stockList: Stock[] = []
    stock.forEach((item) => {
      const indexMember = member.find(o => o.tsCode === item.tsCode)
      let finaIndicatorItem: FinaIndicator = finaIndicator.find(o => o.tsCode === item.tsCode) || {} as FinaIndicator
      pick(finaIndicatorItem, ['roe'])
      _stockList.push({
        ...item,
        ...company.find(o => o.tsCode === item.tsCode),
        ...indexMember,
        ...finaIndicatorItem,
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
    <!-- <router-link to="/stock-detail">股票详情</router-link> -->
    <StockListTable :data="stockList" />
  </div>
</template>

<style lang='scss' scoped>

</style>
