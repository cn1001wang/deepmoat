<script setup lang="ts">
import type {
  ColDef,
  GridReadyEvent,
  ICellRendererParams,
} from 'ag-grid-community'
import type { FinanceTableResponse, FinanceTableRow } from '@/api/finance'
import { AgGridVue } from 'ag-grid-vue3'
import dayjs from 'dayjs'
import quarterOfYear from 'dayjs/plugin/quarterOfYear'
import { computed, ref, watch } from 'vue'
import { getFinanceTable } from '@/api/finance'

dayjs.extend(quarterOfYear)

// --- 2. 状态变量 -----------------------------------------------------------------

const tsCode = ref('603259.SH')
const years = ref(6)
const status = ref('')
const loading = ref(false)

const periods = ref<string[]>([])
const rowData = ref<FinanceTableRow[]>([])
// --- 3. 辅助函数和样式逻辑 -------------------------------------------------------

/**
 * 根据指标和原始值确定 AG Grid 单元格的 CSS 类
 * @param key 指标键名 (e.g., 'debt_ratio')
 * @param raw 原始数值
 * @returns CSS 类名 (e.g., 'good', 'ok', 'bad')
 */
function getCellClass(key: string, raw: any): string {
  if (raw === null || raw === undefined || Number.isNaN(raw))
    return ''
  const v = Number(raw)

  if (key === 'debt_ratio') {
    if (v <= 50)
      return 'good'
    if (v <= 70)
      return 'ok'
    return 'bad'
  }
  if (key === 'expense_rate') {
    if (v <= 20)
      return 'good'
    if (v <= 35)
      return 'ok'
    return 'bad'
  }
  if (
    ['gross_margin', 'net_margin', 'operating_profit_margin', 'roe', 'revenue_yoy', 'assets_yoy'].includes(key)
  ) {
    if (v >= 20)
      return 'good'
    if (v >= 5)
      return 'ok'
    return 'bad'
  }
  if (key === 'operating_cash_flow' || key === 'net_increase_in_cash') {
    return v >= 0 ? 'good' : 'bad'
  }
  return ''
}

/**
 * 格式化数值并返回带 HTML 标签的字符串
 * @param v 数值
 * @param unit 单位 (e.g., '%', '亿', '元')
 * @returns 格式化后的字符串（含 HTML span 标签）
 */
function formatValue(v: any, unit: string): string {
  if (v === null || v === undefined || Number.isNaN(v)) {
    return '<span class="empty">--</span>'
  }
  const n = Number(v)
  let formatted: string

  if (unit === '%')
    formatted = `${n.toFixed(2)}%`
  else if (unit === '亿')
    formatted = `${n.toFixed(2)}亿`
  else if (unit === '元')
    formatted = `${n.toFixed(2)}元`
  else formatted = String(n)

  return formatted
}

/**
 * AG Grid 单元格渲染器，用于自定义格式和样式
 */
function metricValueRenderer(params: ICellRendererParams): string {
  // params.colDef.field 即为 periods 数组中的某个年份字符串
  const periodKey = params.colDef!.field as string
  const rowNode = params.data as FinanceTableRow // 获取当前行数据
  const periodIndex = Number(periodKey.split('_')[1])
  const rawValue = rowNode.values[periodIndex]
  const unit = rowNode.unit
  const key = rowNode.key

  // 获取样式类
  const className = getCellClass(key, rawValue)
  // 获取格式化后的值
  const formattedHtml = formatValue(rawValue, unit)

  // 渲染带有样式的 span
  return `<span class="val ${className}">${formattedHtml}</span>`
}

// --- 4. AG Grid 配置 -------------------------------------------------------------

// 默认列定义
const defaultColDef: ColDef = {
  sortable: false, // 禁用排序
  filter: false, // 禁用过滤
  resizable: true, // 允许调整列宽
  flex: 1, // 灵活调整宽度
  minWidth: 110,
}

// 动态计算列定义
const columnDefs = computed<ColDef[]>(() => {
  // 1. 评价列 (现在移动到第一列)
  const categoryCol: ColDef = {
    headerName: '评价',
    field: 'category',
    pinned: 'left',
    width: 100,
    cellClass: 'category-cell',
    // --- 核心：单元格合并逻辑 ---
    rowSpan: (params) => {
      const data = rowData.value
      const index = params.node?.rowIndex ?? 0
      const currentVal = data[index]?.category

      // 如果当前行和上一行相同，则当前行不渲染（被合并）
      if (index > 0 && currentVal === data[index - 1]?.category) {
        return 1
      }

      // 计算向下有多少行是相同的
      let span = 1
      for (let i = index + 1; i < data.length; i++) {
        if (data[i].category === currentVal) {
          span++
        }
        else {
          break
        }
      }
      return span
    },
    cellStyle: (params) => {
      // 样式微调，确保合并后的文字置顶或居中
      return {
        textAlign: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f9fafb',
        borderRight: '1px solid #e2e8f0',
      }
    },
  }

  // 2. 指标列
  const metricCol: ColDef = {
    headerName: '指标',
    field: 'label',
    pinned: 'left',
    cellClass: 'metric',
    minWidth: 180,
  }

  // 3. 期间列
  const periodCols: ColDef[] = periods.value.map((p, i) => ({
    headerName: p,
    field: `${p}_${i}`,
    cellRenderer: metricValueRenderer,
    cellStyle: { textAlign: 'right' },
  }))

  // 返回新顺序：评价 -> 指标 -> 期间
  return [categoryCol, metricCol, ...periodCols]
})

// Grid Ready 事件（可选，用于 API 访问）
let gridApi: any = null
function onGridReady(params: GridReadyEvent) {
  gridApi = params.api
  // 自动调整第一列（指标列）宽度以适应内容
  // const allColumnIds = params.columnApi.getColumns()?.map(col => col.getColId()) || [];
  // params.columnApi.autoSizeColumns(allColumnIds.slice(0, 1));
}

// --- 5. 数据加载逻辑 -------------------------------------------------------------

async function load() {
  if (!tsCode.value) {
    status.value = '请输入 ts_code'
    return
  }

  loading.value = true
  status.value = '加载中…'
  periods.value = []
  rowData.value = []

  try {
    const res = await getFinanceTable(tsCode.value, years.value)
    const data: FinanceTableResponse = { periods: [], rows: [] }
    res.data.rows.forEach((row) => {
      data.rows.push({
        ...row,
        values: [],
      })
    })

    const q = dayjs().quarter() - 1
    const y = dayjs().year()
    res.data.periods.forEach((p, i) => {
      const d = dayjs(p)

      if ((d.year() === y && d.quarter() >= q) || (d.year() !== y && d.quarter() === 4)) {
        data.periods.push(p)

        res.data.rows.forEach((row, j) => {
          data.rows[j].values.push(row.values[i])
        })
      }
    })

    status.value = ''
    periods.value = data.periods || []
    rowData.value = data.rows || [] // 更新 rowData
  }
  catch (e) {
    status.value = '网络或服务错误'
    console.error(e)
  }
  finally {
    loading.value = false
  }
}

// 组件加载后自动加载数据
load()
watch(years, load) // years 变化时重新加载
</script>

<template>
  <div class="container">
    <div class="toolbar">
      <input v-model="tsCode" placeholder="输入 ts_code，如 603259.SH">
      <input v-model.number="years" type="number" min="3" max="10">
      <button :disabled="loading" @click="load">查询</button>
      <span>{{ status }}</span>
    </div>

    <div class="table-wrap">
      <AgGridVue
        style="width: 100%; height: 100%;"
        :column-defs="columnDefs"
        :row-data="rowData"
        :default-col-def="defaultColDef"
        :row-selection="{ mode: 'multiRow' }"
        :suppress-row-transform="true"
        :animate-rows="true"
        @grid-ready="onGridReady"
      />
    </div>
  </div>
</template>

<style scoped>
/* 保持原有的全局样式，但去除与 AG Grid 冲突的表格样式 */
.container {
  margin: 32px auto;
  padding: 0 16px;
  width: 100%;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

input,
button {
  font-size: 14px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #d0d5dd;
}

button {
  background: #1677ff;
  color: #fff;
  border: 1px solid #1677ff;
  cursor: pointer;
}

button:disabled {
  background: #9bbcf8;
  border-color: #9bbcf8;
  cursor: not-allowed;
}
.table-wrap{
    height: 800px;
    width: 100%;
}
</style>
