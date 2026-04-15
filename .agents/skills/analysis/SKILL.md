---
name: analysis
description: 对话式公司分析技能。只负责“巴菲特/芒格/本杰明”角色化问答与推理，不再生成前置投资裁决和12模块结构化报告。输出中文。
---

# analysis

当用户要“像股东大会一样聊透一家公司”时使用本 skill。
本 skill 只做专业对话分析，不做结构化报告生成。

## 角色边界

- `analysis`：角色对话与判断推进。
- `12-report`：12 模式结构化报告。
- `value-report`：深度模板化研究与评分卡。

如果用户要结构化报告，先调用 `12-report` 或 `value-report`，再进入 `analysis`。

## 先读什么

1. `app/models/models.py`（必须先看；真实表名以此为准）
2. [references/combo-workflow.md](references/combo-workflow.md)
3. [references/dialogue-style.md](references/dialogue-style.md)
4. [references/knowledge-base.md](references/knowledge-base.md)

## 数据顺序（硬规则）

默认顺序：`tushare-data -> deepmoat-local-data -> analysis`

- 核心表至少合并 `income`、`balancesheet`、`cashflow`、`daily_basic`。
- 可选补充 `fina_indicator`、`fina_audit`、`dividend`。
- 必须明确“价格日期”和“财报日期”。

## 输出套路（固定）

固定使用以下四段，不再包含“投资裁决”与“12模块结构化报告”：

1. `【巴菲特开场：公司基本信息】`
2. `【投资者问答：沃伦与查理】`
3. `【本杰明插话：估值校准】`
4. `【综合收束】`

### 开场硬约束

`【巴菲特开场：公司基本信息】` 必须先给 6 项，参考 `skills/value-report/SKILL.md` 的信息口径：

1. 公司如何赚钱（一句话）
2. 收入结构与核心业务占比
3. 行业位置与主要对手
4. 近 4-5 年增长与盈利趋势
5. 资产负债与现金流安全性
6. 当前估值位置（历史分位或同业对比）

### 问答硬约束

- 默认 4-6 个核心问题。
- 每题顺序固定：`投资者 -> 沃伦 -> 查理`。
- 涉及价格时插入 `本杰明`。
- 每一问必须推进判断，不允许泛泛复述。

## 产物落地

- 输出目录：`outputs/`
- 命名建议：`{ts_code}-{name}-{datetime}-analysis.md`
- 例如：`000513.SZ-丽珠集团-20260415-2130-analysis.md`

## 免责声明

> ⚠️ **免责声明**：本分析仅供教育和研究用途，不构成投资建议。角色化表达仅为分析框架，不代表真实人物对个股的实际发言。
