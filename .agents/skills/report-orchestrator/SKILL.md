---
name: report-orchestrator
description: DeepMoat 报告总控技能。用于在 analysis、12-report、value-report 之间做路由分流、执行顺序编排与统一输出短文件名。
---

# report-orchestrator

## 目标

- 在 `analysis`、`12-report`、`value-report` 之间统一分流。
- 统一输出短命名，确保文件名简洁且可读。
- 多 skill 串联时，补一个索引文件记录本次产物清单。

## 路由规则（固定）

1. 用户要“对话式聊透公司/像股东会问答”  
- 路由：`tushare-data -> deepmoat-local-data -> analysis`

2. 用户要“12模块/标准化/模板化研报”  
- 路由：`tushare-data -> deepmoat-local-data -> 12-report`

3. 用户要“终极三问/评分100分/护城河深度研究”  
- 路由：`tushare-data -> deepmoat-local-data -> value-report`

4. 用户同时要“结构化 + 对话”  
- 路由：`tushare-data -> deepmoat-local-data -> 12-report -> analysis`

默认不要并行触发 `analysis + 12-report + value-report`。

## 数据口径（硬规则）

- 必须先看数据库定义：`app/models/models.py`。
- 核心表口径：`income`、`balancesheet`、`cashflow`、`daily_basic`。
- 需要“最新/当前/今日”时，用绝对日期。

## 统一命名规则（硬规则）

`outputs/` 下统一格式：

`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`

artifact 约定：

- `analysis` -> 无
- `12-report` -> 无
- `value-report` -> `draft` 或 `report`
- `report-orchestrator` -> 无

示例：

- `analysis_000513_丽珠集团_2604152130.md`
- `r12_000513_丽珠集团_2604152130.md`
- `value_000513_丽珠集团_2604152130.md`
- `value_000513_丽珠集团_2604152130_draft.md`
- `index_000513_丽珠集团_2604152130.md`

## 多技能串联时的索引文件

若一次任务触发多个子 skill，额外生成：

`index_{symbol}_{name}_{YYMMDDHHmm}.md`

索引文件最少包含：

1. 本次执行链路（按顺序）
2. 每个产物文件名
3. 每个产物对应 skill
