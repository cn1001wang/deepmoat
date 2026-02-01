<!--  -->
<script setup lang="ts">
import type { IndustryTreeNode } from '@/api/finance'
import { onMounted, ref } from 'vue'
import { buildIndustryTree, getSWIndustry } from '@/api/finance'
import IndustryTree from '@/components/IndustryTree.vue'

const industryTree = ref<IndustryTreeNode[]>([])

onMounted(() => {
  getSWIndustry().then((res) => {
    industryTree.value = buildIndustryTree(res.data)
  })
})
</script>

<template>
  <div class="p-28px h-full">
    <IndustryTree :data="industryTree" />
  </div>
</template>

<style lang='scss' scoped>

</style>
