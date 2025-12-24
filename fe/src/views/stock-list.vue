<!--  -->
<script setup lang="ts">
import type { Stock } from '@/api/finance'
import { onMounted, ref } from 'vue'
import { getIndexMember, getStockBasicAll, getStockCompany, getSWIndustry } from '@/api/finance'
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
function loadData() {
  Promise.all([getSWIndustry(), getStockBasicAll(), getIndexMember(), getStockCompany()]).then((res) => {
    const [{ data: industry }, { data: stock }, { data: member }, { data: company }] = res
    const _stockList: Stock[] = []
    stock.forEach((item) => {
      const indexMember = member.find(o => o.tsCode === item.tsCode)
      _stockList.push({
        ...item,
        ...company.find(o => o.tsCode === item.tsCode),
        ...indexMember,
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
