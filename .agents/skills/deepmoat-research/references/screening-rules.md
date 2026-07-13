# 筛选规则

> 排雷 + 策略模板筛选 + 参数接口。排雷规则对齐投资体系 v2 第四章（含"捡漏"模式放宽标注）。

## 第一步：排雷

### 硬性剔除（直接拉黑）

| 排雷条件 | 数据源 | 适用模式 |
|---------|--------|---------|
| ST、*ST、退市风险警示 | `stock_basic.name` 含 ST/*ST | 全部模式 |
| 非标准审计意见 | `fina_audit.audit_result` 非标准无保留 | 全部模式 |
| 最近 3 年扣非净利润连续为负 | `fina_indicator.dt_net_profit` / `income.n_income_attr_p` | 稳健/成长剔除；**捡漏模式放宽到"看到反转信号"** |
| 大股东资金占用 / 关联交易复杂 | 公告/年报 | 全部模式 |
| 频繁并购、频繁改名、频繁跨界 | 公告/年报 | 全部模式 |
| 大股东高比例质押 > 50% | 质押数据 | 全部模式剔除；> 30% 标记风险 |
| 商誉 / 净资产 > 30% | `balancesheet.goodwill` / `total_hldr_eqy_exc_min_int` | 稳健模式剔除；**捡漏模式标记风险后允许进入** |
| 资产负债率 > 70%（金融、地产、公用事业除外） | `fina_indicator.debt_to_assets` / `balancesheet.total_liab/total_assets` | 稳健模式剔除；**捡漏模式重点关注偿债能力** |
| 最近 5 年经营现金流累计为负 | `cashflow.n_cashflow_act` | 全部模式剔除 |

### 警示信号（标记不剔除）

- 经营现金流长期 < 净利润
- 应收账款增速连续高于营收增速（最近 2 年）
- 存货增速连续高于营收增速（最近 2 年）
- 频繁财务调整、会计估计变更
- 高管频繁变动 / 离职潮

### 捡漏 vs 价值陷阱

- 捡漏：错杀，基本面没坏，只是市场暂时不给估值。
- 价值陷阱：基本面在悄悄变坏，看起来便宜但越买越便宜。
- 判定关键：问"为什么便宜"和"什么会让它不再便宜"，两个问题都答得上来才是捡漏。
- 不是捡漏的场景：ST/退市风险/造假嫌疑——这些是接飞刀，不是捡漏。

## 第二步：策略模板筛选

### 1. 稳健价值型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| ROE 均值 | 最近 5 年 > 10% | `fina_indicator.roe` |
| 扣非净利润 | 最近 5 年至少 4 年为正 | `fina_indicator.dt_net_profit` |
| 现金流 / 净利润 | 5 年累计 > 0.8 | `cashflow.n_cashflow_act / income.n_income_attr_p` |
| 经营现金流 | 最近 5 年至少 4 年为正 | `cashflow.n_cashflow_act` |
| 资产负债率 | < 60% | `fina_indicator.debt_to_assets` |
| 商誉 / 净资产 | < 20% | `balancesheet` |
| 估值 | PE < 5 年中位数 或 PB < 5 年中位数 | `daily_basic.pe_ttm, pb` |
| 股息率 | > 2% 或 FCF 收益率 > 5% | `daily_basic.dv_ttm`, `fina_indicator.fcff` |

### 2. 高质量成长型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| ROE 均值 | 最近 5 年 > 15% | `fina_indicator.roe` |
| 营收 CAGR | 最近 5 年 > 8% | `income.revenue` |
| 扣非净利 CAGR | 最近 5 年 > 8% | `fina_indicator.dt_net_profit` |
| 毛利率 | 稳定或提升（5 年标准差 < 5pp 或上升） | `fina_indicator.grossprofit_margin` |
| 现金流 / 净利润 | > 0.8 | `cashflow / income` |
| 资产负债率 | < 60% | `fina_indicator.debt_to_assets` |

### 3. 高股息低估值型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| 股息率 | > 3% | `daily_basic.dv_ttm` |
| 连续分红 | 最近 5 年每年都有分红 | `dividend` |
| 经营现金流 | 最近 5 年均为正 | `cashflow.n_cashflow_act` |
| 估值分位 | PE 或 PB 处于近 5 年 30% 以下分位 | `daily_basic` 历史 |
| 主营稳定 | 营收无连续 2 年下滑 | `income.revenue` |

### 4. 困境反转型

| 指标 | 条件 | 数据源 |
|------|------|--------|
| 利润周期位 | 当前净利率 < 5 年均值的 60% | `fina_indicator.netprofit_margin` |
| 利润修复 | 最近 1-2 季度毛利率或净利率环比改善 | `fina_indicator` 季度 |
| 现金流 | 最近 4 季度经营现金流无明显恶化（不连续为负） | `cashflow` |
| 负债安全 | 资产负债率 < 70%，有息负债/总资产 < 40% | `balancesheet` |
| 估值底部 | PB < 5 年 20% 分位 或 PE < 5 年 20% 分位 | `daily_basic` 历史 |

## 参数配置接口

所有阈值均可由用户覆盖：

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

## 输出格式

```markdown
# 筛选结果：{策略名称}

## 筛选规则
[列出本次使用的参数]

## 排雷统计
- 全市场：{N} 只
- 排雷剔除：{M} 只
- 进入评分：{K} 只

## 观察池总表
| 排名 | 代码 | 名称 | 行业 | ROE均值 | 营收CAGR | 现金流/净利 | 负债率 | PE | PB | 股息率 | 评分 |

## 逐股分析
### {公司名} {代码}
#### 入选理由
- ...（必须引用具体数据）
#### 风险标记
- ...
#### 评分明细
- 财务质量：xx/25
- 现金流质量：xx/25
- 资产安全性：xx/20
- 成长空间：xx/15
- 估值边际：xx/15
- **总分：xx/100**
```
