import request from './request'

export interface ValuationResult {
  analysis: string
  model_used: string
  generated_at: string
}

export interface ValuationSaveResult {
  path: string
}

export function generateValuation(tsCode: string) {
  return request<ValuationResult>({
    url: '/api/ai/valuation',
    method: 'POST',
    data: { ts_code: tsCode },
  })
}

export function saveValuation(tsCode: string, content: string) {
  return request<ValuationSaveResult>({
    url: '/api/ai/valuation/save',
    method: 'POST',
    data: { ts_code: tsCode, content },
  })
}
