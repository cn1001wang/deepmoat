# Repo Agent Rules

## Skills Path Policy

- Always resolve project skills from repository-local `.agents/skills/`.
- Do not read project skills from global `~/.codex/skills/`.
- If a skill name exists in both places, always prefer the repository copy.
- `.claude/skills`、`.trae/skills`、`.codex/skills` 下均为指向 `.agents/skills` 的本地映射文件，由 `scripts/ensure_repo_skills.py` 生成，勿手动编辑；新增/删除 skill 后重跑该脚本即可同步。

## Cross-Platform

- Keep all skill paths relative to the repository root.
- Avoid machine-specific absolute paths (for example `/Users/...` or `C:\Users\...`) in repo configs.

## 投资研究 skill

- 唯一研究入口：`.agents/skills/deepmoat-research/`，整合排雷筛选 / 对话分析 / 结构化研报 / 深度估值四种模式与工作流路由。
- 方法论依据：`C:\codes\github\deepvalue\投资体系\投资体系_v2.md`（排雷 -> 三表 -> 成长 -> 护城河 -> 估值 -> 评分 -> 买入/卖出 -> 组合/复盘）。
- 默认不并行触发多模式，避免重复输出；结论分层表达（重点研究 / 观察 / 高风险观察 / 暂不建议），不下买卖指令。
- 数据层：默认 `tushare-data`；仅批量（≥20 只）或速度优先时启用 `deepmoat-local-data`，并对关键结论用 `tushare-data` 回补校验。启用本地数据前必须先看 `app/models/models.py`。

## 投资研究输出命名规范（Single Source of Truth）

> 所有投资研究产物的文件命名以此为准。`deepmoat-research` skill 不再重复定义。

### 根目录

`outputs/reports/`

### 个股报告

- 目录：`outputs/reports/{symbol}_{name}/`
  - `symbol`：6 位股票代码，不带 `.SH/.SZ`
  - `name`：公司简称（中文）
- 文件名：`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`

| 模式 | prefix | artifact | 示例 |
|------|--------|----------|------|
| 对话 | `analysis` | 无 | `analysis_000513_丽珠集团_2604152130.md` |
| 结构化研报 | `r12` | 无 | `r12_000513_丽珠集团_2604152130.md` |
| 深度估值 | `value` | `draft` 或无 | `value_000513_丽珠集团_2604152130_draft.md` |
| AI 估值 | `ai_valuation` | 无 | `ai_valuation_000513_丽珠集团_2606111430.md` |
| 索引文件 | `index` | 无 | `index_000513_丽珠集团_2604152130.md` |

### 筛选报告

- 目录：`outputs/reports/screener/`
- 文件名：`screener_{strategy}_{YYMMDDHHmm}.md`
- 示例：`screener_稳健价值型_2606111430.md`

### 图表目录

- 深度估值图表：`outputs/reports/{symbol}_{name}/charts/`
- 图表文件：`chart_01.svg`, `chart_02.svg`, ...

### 通用约定

- 统一使用下划线 `_` 分隔，不使用连字符 `-`
- 时间戳格式：`YYMMDDHHmm`（2 位年+月+日+时+分）
- `artifact` 仅在需要区分草稿/中间产物时追加
- 同一只股票的所有产物必须落在同一股票目录中
- 多模式串联时生成索引文件 `index_{symbol}_{name}_{YYMMDDHHmm}.md`，记录执行链路、产物文件名与对应模式

### 示例

```
outputs/reports/000513_丽珠集团/analysis_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/r12_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130_draft.md
outputs/reports/000513_丽珠集团/ai_valuation_000513_丽珠集团_2606111430.md
outputs/reports/000513_丽珠集团/charts/chart_01.svg
outputs/reports/screener/screener_稳健价值型_2606111430.md
```
