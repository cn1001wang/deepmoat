<script setup lang="ts">
import type { IndustryTreeNode } from '@/api/finance'
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  node: IndustryTreeNode
  selectedCode: string | null
}>()

const emit = defineEmits<{
  (e: 'select', node: IndustryTreeNode): void
}>()

const expanded = ref(true)

const hasChildren = computed(
  () => props.node.children && props.node.children.length > 0,
)

const isSelected = computed(
  () => props.selectedCode === props.node.industryCode,
)

// 选中子节点时，自动展开父节点
watch(
  () => props.selectedCode,
  (code) => {
    if (
      hasChildren.value
      && props.node.children!.some(c => c.industryCode === code)
    ) {
      expanded.value = true
    }
  },
)

function toggle() {
  expanded.value = !expanded.value
}

function selectNode() {
  expanded.value = true
  emit('select', props.node)
}
</script>

<template>
  <li>
    <div
      class="node-row"
      :class="{ selected: isSelected }"
      @click="selectNode"
    >
      <span
        v-if="hasChildren"
        class="arrow"
        @click.stop="toggle"
      >
        {{ expanded ? '▾' : '▸' }}
      </span>
      <span v-else class="arrow-placeholder" />

      <span class="label" :class="node.level.toLowerCase()">
        {{ node.industryName }}
      </span>
    </div>

    <ul v-if="expanded && hasChildren" class="children">
      <IndustryTreeNodeItem
        v-for="child in node.children"
        :key="child.industryCode"
        :node="child"
        :selected-code="selectedCode"
        @select="$emit('select', $event)"
      />
    </ul>
  </li>
</template>

<style scoped>
.node-row {
  display: flex;
  align-items: center;
  height: 32px;
  padding: 0 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.node-row:hover {
  background: #eef3ff;
}

.node-row.selected {
  background: #e6f0ff;
  color: #1677ff;
  font-weight: 600;
}

.arrow,
.arrow-placeholder {
  width: 18px;
  text-align: center;
  color: #666;
}

.label {
  white-space: nowrap;
}

.label.l1 {
  font-size: 14px;
}

.label.l2 {
  font-size: 13px;
  margin-left: 4px;
}

.label.l3 {
  font-size: 12px;
  margin-left: 8px;
  color: #666;
}

.children {
  padding-left: 16px;
  list-style: none;
  margin: 2px 0;
}
</style>
