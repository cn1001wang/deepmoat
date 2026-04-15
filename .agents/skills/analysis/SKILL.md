---
name: analysis
description: 对话式公司分析技能。用于“像股东会问答一样聊透公司”的场景，只输出巴菲特/芒格/本杰明角色化分析，不输出12模块结构化报告或深度评分卡。输出中文，并按统一命名规范落盘到 outputs。
---

# analysis

## 职责边界

- 仅做角色化问答分析：`投资者 -> 沃伦 -> 查理`，涉估值时加入 `本杰明`。
- 不产出 12 模块结构化报告。
- 不产出 100 分评分卡。
- 若用户要求结构化报告，先走 `12-report` 或 `value-report`，再回到本 skill。

## 前置顺序（硬规则）

`tushare-data -> deepmoat-local-data -> analysis`

- 必须先查看数据库定义：`app/models/models.py`。
- 核心表至少合并：`income`、`balancesheet`、`cashflow`、`daily_basic`。
- 必须给出“价格日期”和“财报日期”。

## 读取参考

1. `app/models/models.py`
2. [references/combo-workflow.md](references/combo-workflow.md)
3. [references/dialogue-style.md](references/dialogue-style.md)
4. [references/knowledge-base.md](references/knowledge-base.md)

## 输出结构（固定）

固定四段：

1. `【巴菲特开场：公司基本信息】`
2. `【投资者问答：沃伦与查理】`
3. `【本杰明插话：估值校准】`
4. `【综合收束】`

开场必须先给 6 项：

1. 公司如何赚钱（一句话）
2. 收入结构与核心业务占比
3. 行业位置与主要对手
4. 近 4-5 年增长与盈利趋势
5. 资产负债与现金流安全性
6. 当前估值位置（历史分位或同业对比）

- 默认 4-6 个核心问题。
- 每题顺序固定：`投资者 -> 沃伦 -> 查理`。
- 涉及价格时插入 `本杰明`。
- 每一问必须推进判断，不允许泛泛复述。

## 输出命名（统一）

- 输出目录：`outputs/`
- 文件名：`skill-analysis--{ts_code}--{name}--{YYYYMMDD-HHmm}--dialogue.md`
- 示例：`skill-analysis--000513-SZ--丽珠集团--20260415-2130--dialogue.md`

## 免责声明

> ⚠️ **免责声明**：本分析仅供教育和研究用途，不构成投资建议。角色化表达仅为分析框架，不代表真实人物对个股的实际发言。
