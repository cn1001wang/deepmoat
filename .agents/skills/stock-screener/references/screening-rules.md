# 筛选规则详细定义

## 第一步：排雷（硬性剔除）

### 直接剔除条件

1. **ST / *ST / 退市风险警示**
   - 数据源：`stock_basic.name` 包含 "ST" 或 "*ST"
   - 规则：直接剔除

2. **非标准审计意见**
   - 数据源：`fina_audit.audit_result`
   - 规则：最近一期审计意见非"标准无保留意见"则剔除

3. **连续亏损**
   - 数据源：`fina_indicator.dt_netprofit_yoy` 或 `income.n_income_attr_p`
   - 规则：最近 3 年扣非净利润连续为负则剔除

4. **经营现金流长期为负**
   - 数据源：`cashflow.n_cashflow_act`
   - 规则：最近 5 年经营现金流累计为负则剔除

5. **商誉过高**
   - 数据源：`balancesheet.goodwill` / `balancesheet.total_hldr_eqy_exc_min_int`
   - 规则：商誉 / 净资产 > 30% 则剔除

6. **资产负债率过高**
   - 数据源：`fina_indicator.debt_to_assets` 或 `balancesheet.total_liab / total_assets`
   - 规则：> 70% 则剔除
   - 例外：金融（银行、保险、券商）、地产、公用事业行业

### 风险标记（不剔除）

7. **大股东高质押**
   - 规则：质押比例 > 30% 标记黄色风险

8. **应收账款异常**
   - 规则：最近 2 年应收账款增速 > 营收增速，标记风险

9. **存货异常**
   - 规则：最近 2 年存货增速 > 营收增速，标记风险

---

## 第二步：策略模板筛选条件

### 稳健价值型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| ROE 均值 | 最近 5 年 > 10% | `fina_indicator.roe` |
| 扣非净利润 | 最近 5 年至少 4 年为正 | `fina_indicator.dt_net_profit` |
| 现金流 / 净利润 | 5 年累计 > 0.8 | `cashflow.n_cashflow_act / income.n_income_attr_p` |
| 经营现金流 | 最近 5 年至少 4 年为正 | `cashflow.n_cashflow_act` |
| 资产负债率 | < 60% | `fina_indicator.debt_to_assets` |
| 商誉 / 净资产 | < 20% | `balancesheet` |
| 估值 | PE < 5年中位数 或 PB < 5年中位数 | `daily_basic.pe_ttm, pb` |
| 股息率 | > 2% 或 FCF收益率 > 5% | `daily_basic.dv_ttm`, `fina_indicator.fcff` |

### 高质量成长型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| ROE 均值 | 最近 5 年 > 15% | `fina_indicator.roe` |
| 营收 CAGR | 最近 5 年 > 8% | `income.revenue` |
| 扣非净利 CAGR | 最近 5 年 > 8% | `fina_indicator.dt_net_profit` |
| 毛利率 | 稳定或提升（5年标准差 < 5pp 或上升趋势） | `fina_indicator.grossprofit_margin` |
| 现金流 / 净利润 | > 0.8 | `cashflow / income` |
| 资产负债率 | < 60% | `fina_indicator.debt_to_assets` |

### 高股息低估值型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| 股息率 | > 3% | `daily_basic.dv_ttm` |
| 连续分红 | 最近 5 年每年都有分红 | `dividend` |
| 经营现金流 | 最近 5 年均为正 | `cashflow.n_cashflow_act` |
| 估值分位 | PE 或 PB 处于近 5 年 30% 以下分位 | `daily_basic` 历史数据 |
| 主营稳定 | 营收无连续 2 年下滑 | `income.revenue` |

### 困境反转型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| 利润周期位 | 当前净利率 < 5年均值的 60% | `fina_indicator.netprofit_margin` |
| 利润修复 | 最近 1-2 季度毛利率或净利率环比改善 | `fina_indicator` 季度数据 |
| 现金流 | 最近 4 季度经营现金流无明显恶化（不连续为负） | `cashflow` |
| 负债安全 | 资产负债率 < 70%，有息负债/总资产 < 40% | `balancesheet` |
| 估值底部 | PB < 5年 20% 分位 或 PE < 5年 20% 分位 | `daily_basic` 历史 |

---

## 参数配置接口

所有筛选条件的阈值均可通过参数覆盖：

```json
{
  "strategy": "稳健价值型",
  "params": {
    "min_roe": 10,
    "max_debt_ratio": 60,
    "min_cashflow_ratio": 0.8,
    "max_goodwill_ratio": 20,
    "min_dividend_yield": 2,
    "years": 5,
    "exclude_industries": ["银行", "保险", "券商", "房地产"]
  }
}
```
