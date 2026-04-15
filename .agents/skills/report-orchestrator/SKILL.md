---
name: report-orchestrator
description: DeepMoat 报告总控技能。用于在 analysis、12-report、value-report 之间做路由分流、执行顺序编排与统一输出命名，确保 outputs 文件名可直接识别来源 skill。
---

# report-orchestrator

## 目标

- 在 `analysis`、`12-report`、`value-report` 之间统一分流。
- 统一输出命名，确保文件名可直接识别来源 skill。
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

`skill-{skill_name}--{ts_code}--{name}--{YYYYMMDD-HHmm}--{artifact}.md`

artifact 约定：

- `analysis` -> `dialogue`
- `12-report` -> `report`
- `value-report` -> `draft` 或 `report`
- `report-orchestrator` -> `index`

示例：

- `skill-analysis--000513-SZ--丽珠集团--20260415-2130--dialogue.md`
- `skill-12-report--000513-SZ--丽珠集团--20260415-2130--report.md`
- `skill-value-report--000513-SZ--丽珠集团--20260415-2130--report.md`
- `skill-report-orchestrator--000513-SZ--丽珠集团--20260415-2130--index.md`

## 多技能串联时的索引文件

若一次任务触发多个子 skill，额外生成：

`skill-report-orchestrator--{ts_code}--{name}--{YYYYMMDD-HHmm}--index.md`

索引文件最少包含：

1. 本次执行链路（按顺序）
2. 每个产物文件名
3. 每个产物对应 skill
