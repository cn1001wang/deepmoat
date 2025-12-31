<script setup lang="ts">
import type { ColDef } from 'ag-grid-community'
import type { Stock } from '@/api/finance'
import { AgGridVue } from 'ag-grid-vue3'
import { useRouter } from 'vue-router';

const router = useRouter()

const props = defineProps<{
  data: Stock[]
}>()

/**
 * 核心逻辑：隐藏重复的单元格文字
 * 使用 previousSibling 避开 Grid API 渲染冲突错误 #252
 */
const cellClassRules = {
  'cell-span-hidden': (params: any) => {
    const field = params.colDef.field as keyof Stock
    const value = params.value
    // 直接通过节点链表获取上一行，不触发 API 重绘
    const prevNode = params.node.previousSibling
    return prevNode && value === prevNode.data?.[field]
  },
}

const defaultColDef: ColDef = {
  resizable: true,
  sortable: true,
  // 设置背景色防止文字重叠，设置 flex 基础占比
  cellStyle: { display: 'flex', alignItems: 'center', backgroundColor: 'white' },
}

const columnDefs: ColDef[] = [
  {
    headerName: '一级行业',
    field: 'l1Name',
    width: 180,
    valueFormatter: params => params.value ? `${params.value} (${params.data?.l1Code})` : '',
    cellClassRules,
    // 关键：定义过滤器搜索的数据范围
    filterValueGetter: (params) => {
      const name = params.data?.l1Name || ''
      const code = params.data?.l1Code || ''
      // 返回一个包含名称和代码的合并字符串，这样过滤器就能同时匹配两者
      return `${name} ${code}`
    },

    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
      // 建议：设为 true，这样用户输入 "801" 就能匹配到包含该代码的行业
      // filterOptions: ['contains', 'notContains', 'equals'],
      debounceMs: 500,
    },
  },
  {
    headerName: '二级行业',
    field: 'l2Name',
    width: 180,
    valueFormatter: params => params.value ? `${params.value} (${params.data?.l2Code})` : '',
    cellClassRules,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '三级行业',
    field: 'l3Name',
    width: 200,
    valueFormatter: params => params.value ? `${params.value} (${params.data?.l3Code})` : '',
    cellClassRules,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '股票名称',
    field: 'name',
    width: 120,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
    // flex: 1,
    cellRenderer: (params:any) => {
      const div = document.createElement('div');
      div.style.cursor = 'pointer'; // 鼠标样式
      div.style.color = '#1890ff';  // 可选：蓝色表示可点击
      div.textContent = params.value;

      div.addEventListener('click', () => {
        // 跳转到详情页，比如用 Vue Router
        router.push(`/stock/${encodeURIComponent(params.data.tsCode)}`);
      });

      return div;
    }
  },
  {
    headerName: '股票代码',
    field: 'tsCode',
    width: 120,
    filter: 'agTextColumnFilter', // 显式指定文本过滤
    filterParams: {
      buttons: ['reset', 'apply'], // 增加重置和应用按钮
      closeOnApply: true,
    },
  },
  {
    headerName: '公司全称',
    field: 'comName',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '公司介绍',
    field: 'introduction',
    width: 300,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '主要业务及产品',
    field: 'mainBusiness',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '统一社会信用代码',
    field: 'comId',
    width: 180,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '交易所',
    field: 'exchange',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '法人代表',
    field: 'chairman',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '总经理',
    field: 'manager',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '董秘',
    field: 'secretary',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '注册资本(万元)',
    field: 'regCapital',
    width: 130,
    filter: 'agNumberColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '注册日期',
    field: 'setupDate',
    width: 120,
    filter: 'agDateColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '所在省份',
    field: 'province',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '所在城市',
    field: 'city',
    width: 100,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '公司主页',
    field: 'website',
    width: 160,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    cellRenderer: (params: any) =>
      params.value ? `<a href="${params.value.startsWith('http') ? params.value : `https://${params.value}`}" target="_blank">${params.value}</a>` : '',
  },
  {
    headerName: '电子邮件',
    field: 'email',
    width: 160,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '办公室',
    field: 'office',
    width: 200,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '员工人数',
    field: 'employees',
    width: 100,
    filter: 'agNumberColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
  },
  {
    headerName: '主要业务及产品',
    field: 'mainBusiness',
    width: 260,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
  },
  {
    headerName: '经营范围',
    field: 'businessScope',
    width: 300,
    filter: 'agTextColumnFilter',
    filterParams: {
      buttons: ['reset', 'apply'],
      closeOnApply: true,
    },
    tooltipValueGetter: params => params.value,
    cellClass: 'text-ellipsis', // 添加类名
  },
]
</script>

<template>
  <div class="industry-grid-wrapper">
    <AgGridVue
      class="ag-theme-alpine"
      style="width: 100%; height: 800px"
      :column-defs="columnDefs"
      :row-data="data"
      :default-col-def="defaultColDef"
      :suppress-row-transform="true"
      :animate-rows="true"
      :enable-cell-text-selection="true"
      :ensure-dom-order="true"
    />
  </div>
</template>

<style scoped>
/* 关键：将重复的行业文字设为透明，视觉上实现合并效果 */
:deep(.cell-span-hidden) {
  color: transparent !important;
  /* 移除重复单元格的下边框，让这一组看起来像在一个大框里 */
  border-bottom: none !important;
}

/* 优化表格线条 */
.ag-theme-alpine {
  --ag-border-color: #e2e2e2;
}

:deep(.ag-cell) {
  border-right: 1px solid #eee !important;
}

.industry-grid-wrapper {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}
</style>
