import request from './request'

export interface FinanceTableRow {
  category: string
  key: string
  label: string
  unit: string
  values: number[]
}
export interface FinanceTableResponse {
  periods: string[]
  rows: FinanceTableRow[]
}
export interface SwIndustry {
  indexCode: string
  industryCode: string
  industryName: string
  parentCode: string
  isPub: string
  level: string
  src: string
}

export interface StockBasic {
  tsCode: string
  symbol: string
  name: string
  fullname: string
  ennname: string
  cnspell: string
  area: string
  industry: string
  market: string
  exchange: string
  currType: string
  listStatus: string
  listDate: string
  delistDate: string
  isHs: string
  actName: string
  actEntType: string
}

export interface IndexMember {
  l1Code: string
  l1Name: string
  l2Code: string
  l2Name: string
  l3Code: string
  l3Name: string
  tsCode: string
  name: string
  inDate: string
  outDate: string
  isNew: string
}

export interface StockCompany {
  tsCode: string
  comName?: string
  comId?: string
  exchange?: string
  chairman?: string
  manager?: string
  secretary?: string
  regCapital?: number
  setupDate?: string
  province?: string
  city?: string
  website?: string
  email?: string
  employees?: number
}

// export type Stock = StockBasic & Partial<IndexMember>
export interface Stock extends StockBasic, Partial<Omit<IndexMember, 'tsCode' | 'name'>>, Partial<Omit<StockCompany, 'tsCode' | 'exchange'>> {
  // 这样既保留了 StockBasic 的必选 name，又引入了 IndexMember 的其他可选行业字段
}

export function getFinanceTable(tsCode: string, years: string | number) {
  return request<FinanceTableResponse>(
    `/api/finance/table?ts_code=${encodeURIComponent(tsCode)}&years=${years}`,
  )
}

export function getSWIndustry() {
  return request<SwIndustry[]>(`/api/sw_industry`)
}

export function getStockBasicAll() {
  return request<StockBasic[]>(`/api/stock_basic_all`)
}

export function getIndexMember() {
  return request<IndexMember[]>(`/api/index_member`)
}

export function getStockCompany() {
  return request<StockCompany[]>(`/api/company`)
}
