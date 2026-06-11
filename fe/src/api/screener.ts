import request from './request'

export interface ScreenerStock {
  tsCode: string
  name: string
  industry: string | null
  avgRoe: number
  debtRatio: number | null
  cashflowRatio: number | null
  score: number
  risks: Array<{ type: string; detail: string; severity: string }>
}

export interface ScreenerMeta {
  total: number
  eliminated: number
  passed: number
  strategy: string
  config: Record<string, number>
}

export interface ScreenerResult {
  stocks: ScreenerStock[]
  meta: ScreenerMeta
}

export interface RiskCheckResult {
  passed: boolean
  risks: Array<{ type: string; detail: string; severity: string }>
}

export interface ScreenerParams {
  min_roe?: number
  max_debt_ratio?: number
  min_cashflow_ratio?: number
  max_goodwill_ratio?: number
  min_dividend_yield?: number
}

export function runScreener(strategy: string, params?: ScreenerParams, years = 5) {
  return request<ScreenerResult>({
    url: '/api/screener/run',
    method: 'POST',
    data: { strategy, params, years },
  })
}

export function checkRisk(tsCode: string) {
  return request<RiskCheckResult>(`/api/screener/risk-check?ts_code=${encodeURIComponent(tsCode)}`)
}
