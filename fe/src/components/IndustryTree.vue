<script setup lang="ts">
import type { IndustryTreeNode } from '@/api/finance'
import { ref } from 'vue'
import IndustryTreeNodeItem from './IndustryTreeNodeItem.vue'

defineProps<{
  data: IndustryTreeNode[]
}>()

const emit = defineEmits<{
  (e: 'update:selected', node: IndustryTreeNode): void
}>()

const selectedCode = ref<string | null>(null)

function handleSelect(node: IndustryTreeNode) {
  selectedCode.value = node.industryCode
  emit('update:selected', node)
}
</script>

<template>
  <ul class="industry-tree">
    <IndustryTreeNodeItem
      v-for="node in data"
      :key="node.industryCode"
      :node="node"
      :selected-code="selectedCode"
      @select="handleSelect"
    />
  </ul>
</template>

<style scoped>
.industry-tree {
  padding: 8px;
  margin: 0;
  list-style: none;
  background: #fafafa;
  border-radius: 8px;
}
</style>
