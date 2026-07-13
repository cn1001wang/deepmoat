---
name: deepmoat-research
description: DeepMoat 投资研究核心技能。基于价值投资体系 v2，统一排雷筛选、对话分析、结构化研报、深度估值评分的全流程，按投资阶段路由并按统一命名规范落盘到 outputs。输出中文。
---

# deepmoat-research

> 本 skill 是 DeepMoat 投资研究的唯一入口，整合了原 `workflow-orchestrator` / `stock-screener` / `analysis` / `12-report` / `value-report` / `shared-references` 六个零散 skill。
> 方法论依据：`C:\codes\github\deepvalue\投资体系\投资体系_v2.md`（排雷 -> 三表 -> 成长 -> 护城河 -> 估值 -> 评分 -> 买入/卖出 -> 组合/复盘）。
> 输出命名规范见仓库 `AGENTS.md`，本 skill 不再重复定义。

## 一句话定位

用工程师的可量化思维 + "知行合一"，在能力圈内以足够便宜的价格买入长期能赚钱的企业；AI 只辅助研究，不下买卖指令。

## 输出模式（四种，互不重叠）

| 模式 | 产物 | 边界 | prefix |
|------|------|------|--------|
| 筛选 | 观察池（排雷+筛选+评分排序） | 只输出观察池与评分，不做单票深度 | `screener` |
| 对话 | 角色化问答（沃伦/查理/本杰明） | 不产出结构化报告、不产出评分卡 | `analysis` |
| 结构化研报 | 12 模块报告 | 不写角色对话、不写 100 分评分卡 | `r12` |
| 深度估值 | 深度价值报告（含评分卡+终极三问+图表） | 最重最深，默认含评分与幸存者偏差检验 | `value` |

- 默认不要并行触发多个模式，避免重复计算与重复文本。
- 用户同时要"结构化 + 对话"：先 `r12`，再 `analysis`。
- 结论分层表达：`重点研究 / 观察 / 高风险观察 / 暂不建议`，不直接下买卖指令。

## 工作流阶段路由（固定）

### 0. 数据层选择（先判定，后路由）

- 默认优先：`tushare-data`（官方实时数据链路）。
- 仅在以下场景启用 `deepmoat-local-data`：
  - 横向比较标的 ≥ 20 只，或全市场批量筛选/排序。
  - 用户明确提出"速度优先/尽快返回"。
- 使用 `deepmoat-local-data` 时，对关键结论需用 `tushare-data` 做日期回补或抽样校验。
- 启用本地数据前必须先看数据库定义：`app/models/models.py`；核心表口径：`income`、`balancesheet`、`cashflow`、`daily_basic`、`fina_indicator`、`dividend`、`fina_audit`、`stock_company`。
- 涉及"最新/当前/今日"必须写绝对日期，并标注"价格日期""财报日期"。

### 1. 排雷 / 筛选 / 观察池

- 触发词：排雷、筛选、筛股票、观察池、帮我找、批量筛、全市场
- 路由：`deepmoat-local-data -> 筛选模式`（筛选天然需全量数据，默认走本地；最终候选用 `tushare-data` 验证）
- 规则详见 [references/screening-rules.md](references/screening-rules.md)、[references/scoring-model.md](references/scoring-model.md)

### 2. 对话式分析

- 触发词：聊透、分析一下、像股东会、问答
- 路由：默认 `tushare-data -> 对话模式`；极速/大批量 `deepmoat-local-data -> 对话模式`（必要时补 tushare-data 校验）
- 规则详见 [references/dialogue-style.md](references/dialogue-style.md)、[references/knowledge-base.md](references/knowledge-base.md)

### 3. 结构化研报

- 触发词：12模块、标准化研报、模板化报告
- 路由：默认 `tushare-data -> 结构化研报模式`；极速/大批量走本地并补校验
- 模板详见 [references/structured-report.md](references/structured-report.md)

### 4. 深度估值 / 评分

- 触发词：终极三问、评分、100分、护城河深度、深度研究
- 路由：默认 `tushare-data -> 深度估值模式`；极速/大批量走本地并补校验
- 分析口径详见 [references/analysis-framework.md](references/analysis-framework.md)

### 5. 结构化 + 对话

- 触发词：用户同时要"结构化 + 对话"
- 路由：`tushare-data -> 结构化研报 -> 对话`

### 6. 全流程（筛选 + 深度分析）

- 触发词：从头开始、完整流程、筛选后深入分析
- 路由：`deepmoat-local-data -> 筛选模式 -> tushare-data -> 深度估值模式`

### 7. 跟踪 / 监控

- 触发词：跟踪、监控、更新、复查、re-score
- 路由：`deepmoat-local-data -> 筛选模式`（比对模式：对比上次评分，输出变化）

## 各模式要点

### 筛选模式

实现体系前三步：排雷 -> 筛好生意 -> 评分排序，输出观察池。

- 第一步排雷（硬性剔除 + 风险标记）：见 screening-rules.md，捡漏模式可按 v2 第四章对部分条件放宽并标注。
- 第二步策略模板筛选：稳健价值型 / 高质量成长型 / 高股息低估值型 / 困境反转型，阈值可覆盖。
- 第三步 100 分制评分：按 v2 第九章 4 模式（稳健价值 / 捡漏型 / 高质量成长 / 护城河型）选择评分模型，见 scoring-model.md。
- 第四步输出观察池总表 + 逐股入选理由（3-5 条 bullet，必须引用具体数据）+ 风险标记 + 评分明细。
- 结论分类 A/B/C/D，不出"买入卖出"。

### 对话模式

固定四段：`【巴菲特开场：公司基本信息】` -> `【投资者问答：沃伦与查理】` -> `【本杰明插话：估值校准】` -> `【综合收束】`。

- 开场必给 6 项：怎么赚钱 / 收入结构 / 行业位置 / 近 4-5 年趋势 / 资产负债与现金流安全性 / 当前估值位置。
- 默认 4-6 个核心问题，每题顺序固定 `投资者 -> 沃伦 -> 查理`，涉及价格插入 `本杰明`。
- 角色化只改变表达方式，不改变证据标准；资料不足要直接承认。

### 结构化研报模式

12 模块固定（公司概览/管理层/商业模式/护城河/财务深度/电话会要点/多模型估值/竞争行业/技术面可选/增长催化剂/风险矩阵/投资决策与跟踪清单），每模块末尾一句"本模块结论"。

- 明确区分：事实 / 计算结果 / 推断。
- 估值必须给数字区间，不可只给"高估/低估"。
- 数据缺口直接写"数据缺失/待核实"。

### 深度估值模式

12 章固定（公司概况/行业竞争/护城河/管理层资本配置/财务分析/成长驱动/风险含幸存者偏差/估值/多空跟踪/最终结论/100分评分/终极三问），每章末尾必须有 `结论：` `事实：` `推断：`。

- 必须回答终极三问：提价 5% 客户是否流失 / 赚的钱有没有被管理层浪费 / 行业最差年份怎么活下来。
- 固定图表流程（硬规则）：先用脚本出图再回插，见下文"脚本"。
- 草稿 -> 图表 -> 正式报告 -> 图表回插。

## 脚本（深度估值模式专用）

固定脚本位于本 skill 根目录（用 `parents[3]` 定位仓库根，勿加额外子目录层）：

- `.agents/skills/deepmoat-research/value_report_scaffold.py`：从本地库生成定量草稿。
- `.agents/skills/deepmoat-research/render_value_report_charts.py`：从草稿生成图表并回插正式报告。

```bash
# 1) 生成草稿
uv run python .agents/skills/deepmoat-research/value_report_scaffold.py <股票代码或名称>

# 2) 生成图表（默认输出到草稿同目录/charts）
uv run python .agents/skills/deepmoat-research/render_value_report_charts.py <草稿md路径>

# 3) 回插图表到正式报告（幂等，覆盖 VALUE_CHARTS_START/END 区块）
uv run python .agents/skills/deepmoat-research/render_value_report_charts.py <草稿md路径> \
  --inject-report <正式报告md路径> --cleanup-intermediate
```

验收规则：正式报告必须出现图表区块；图片链接可打开且用相对路径；图表与正文结论口径一致。

## 共享硬规则

- 默认不并行触发多模式，避免重复输出。
- 数据冲突处理：公共披露新于本地缓存 -> 优先公共披露；本地库更新更晚且可验证 -> 优先本地库；口径冲突必须显式说明，禁止静默混用。
- 外部资料只做"增量验证"，不替代本地财务主口径。
- 失败兜底：本地库缺表先输出可得结论再列缺失项；外部检索失败保留本地定量结论并标注"外部验证不足"；图表脚本失败保留文字结论并附失败命令与错误摘要。
- 每个重要结论尽量说明"可能错在哪里"和"未来看哪些指标验证或推翻"。

## 免责声明

> ⚠️ 本 skill 产出仅供教育和研究用途，不构成投资建议。角色化表达仅为分析框架，不代表真实人物对个股的实际发言。投资决策由用户自行承担。

## references 索引

- [screening-rules.md](references/screening-rules.md)：排雷规则 + 4 策略模板筛选条件 + 参数接口
- [scoring-model.md](references/scoring-model.md)：4 模式 100 分制评分模型 + 结论分类
- [analysis-framework.md](references/analysis-framework.md)：三表分析 / 成长能力 / 护城河 / 估值方法选择口径
- [dialogue-style.md](references/dialogue-style.md)：股东大会问答体规则
- [structured-report.md](references/structured-report.md)：12 模块结构化报告模板
- [knowledge-base.md](references/knowledge-base.md)：巴菲特/芒格知识库使用规则
