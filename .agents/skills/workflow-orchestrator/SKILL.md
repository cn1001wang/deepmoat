---
name: workflow-orchestrator
description: DeepMoat 工作流总控技能。按投资体系阶段（排雷→筛选→分析→估值→跟踪）做路由分流、执行顺序编排与统一输出命名。
---

# workflow-orchestrator

## 目标

- 按投资工作流阶段路由到正确的子技能。
- 统一输出命名，确保文件名简洁可读。
- 多 skill 串联时，补索引文件记录本次产物清单。

## 工作流阶段路由（固定）

### 0. 数据层选择（先判定，后路由）

- 默认优先：`tushare-data`（官方实时数据链路）。
- 仅在以下场景启用 `deepmoat-local-data`：
  - 横向比较标的 ≥ 20 只，或全市场批量筛选/排序。
  - 用户明确提出"速度优先/尽快返回"。
- 使用 `deepmoat-local-data` 时，对关键结论需用 `tushare-data` 做日期回补或抽样校验。

### 1. 排雷 / 筛选 / 观察池

**触发词**：排雷、筛选、筛股票、观察池、帮我找、批量筛、全市场

**路由**：`deepmoat-local-data → stock-screener`

说明：筛选天然需要全量数据，默认走本地。最终候选用 `tushare-data` 验证。

### 2. 对话式分析

**触发词**：聊透、分析一下、像股东会、问答

**路由**：
- 默认：`tushare-data → analysis`
- 极速/大批量：`deepmoat-local-data → analysis`（必要时补 tushare-data 校验）

### 3. 结构化研报

**触发词**：12模块、标准化研报、模板化报告

**路由**：
- 默认：`tushare-data → 12-report`
- 极速/大批量：`deepmoat-local-data → 12-report`（必要时补 tushare-data 校验）

### 4. 深度估值 / 评分

**触发词**：终极三问、评分、100分、护城河深度、深度研究

**路由**：
- 默认：`tushare-data → value-report`
- 极速/大批量：`deepmoat-local-data → value-report`（必要时补 tushare-data 校验）

### 5. 结构化 + 对话

**触发词**：用户同时要"结构化 + 对话"

**路由**：`tushare-data → 12-report → analysis`

### 6. 全流程（筛选 + 深度分析）

**触发词**：从头开始、完整流程、筛选后深入分析

**路由**：`deepmoat-local-data → stock-screener → tushare-data → value-report`

### 7. 跟踪 / 监控

**触发词**：跟踪、监控、更新、复查、re-score

**路由**：`deepmoat-local-data → stock-screener`（比对模式：对比上次评分，输出变化）

---

## 硬规则

- 默认不要并行触发 `analysis + 12-report + value-report`，避免重复输出。
- 必须先看数据库定义：`app/models/models.py`。
- 核心表口径：`income`、`balancesheet`、`cashflow`、`daily_basic`、`fina_indicator`。
- 需要"最新/当前/今日"时，用绝对日期。

## 统一命名规则（硬规则）

统一根目录：`outputs/reports/`

### 个股报告

目录：`outputs/reports/{symbol}_{name}/`

文件：`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`

| 技能 | prefix | artifact |
|------|--------|----------|
| analysis | `analysis` | 无 |
| 12-report | `r12` | 无 |
| value-report | `value` | `draft` 或无 |
| AI 估值 | `ai_valuation` | 无 |

### 筛选报告

目录：`outputs/reports/screener/`

文件：`screener_{strategy}_{YYMMDDHHmm}.md`

### 索引文件

多技能串联时生成：`outputs/reports/{symbol}_{name}/index_{symbol}_{name}_{YYMMDDHHmm}.md`

索引内容：
1. 本次执行链路（按顺序）
2. 每个产物文件名
3. 每个产物对应 skill

### 命名约定

- `symbol` 仅保留 6 位股票代码，不带 `.SH/.SZ`
- 统一使用下划线 `_` 分隔
- `artifact` 只在需要区分草稿时追加

### 示例

```
outputs/reports/000513_丽珠集团/analysis_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/r12_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130_draft.md
outputs/reports/000513_丽珠集团/ai_valuation_000513_丽珠集团_2606111430.md
outputs/reports/screener/screener_稳健价值型_2606111430.md
```
