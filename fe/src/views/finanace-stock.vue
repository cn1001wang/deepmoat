<!--  -->
<script setup lang="ts">
import TsCodeTable from '@/components/TsCodeTable.vue'
defineProps<{tscode: string}>()
</script>

<template>
  <TsCodeTable :tscode="tscode"/>
</template>

<style lang='scss' scoped>

</style>
