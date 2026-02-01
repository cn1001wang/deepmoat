export interface Dividend {
  /** TS代码 */
  tsCode: string
  /** 分红年度 */
  endDate: string
  /** 预案公告日 */
  annDate: string
  /** 实施进度 */
  divProc?: string
  /** 每股送转 */
  stkDiv?: number
  /** 每股送股比例 */
  stkBoRate?: number
  /** 每股转增比例 */
  stkCoRate?: number
  /** 每股分红（税后） */
  cashDiv?: number
  /** 每股分红（税前） */
  cashDivTax?: number
  /** 股权登记日 */
  recordDate?: string
  /** 除权除息日 */
  exDate?: string
  /** 派息日 */
  payDate?: string
  /** 红股上市日 */
  divListdate?: string
  /** 实施公告日 */
  impAnnDate?: string
  /** 基准日 */
  baseDate?: string
  /** 基准股本（万） */
  baseShare?: number
}
