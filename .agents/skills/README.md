# Repo Skills

仓库内技能统一放在 `.agents/skills/`。

## 总控与子技能

- `report-orchestrator/`：总控 skill，只做路由编排与输出命名规范。
- `analysis/`：角色化对话分析（巴菲特/芒格/本杰明），不产出 12 模块报告。
- `12-report/`：12 模式结构化报告，不产出角色对话。
- `value-report/`：深度价值研究模板（含评分卡与终极三问）。
- `deepmoat-local-data/`：读取本地数据库与本地 HTTP 接口，补充外部 `tushare-data`。

## 标准流程

- 只要对话：`report-orchestrator -> tushare-data -> deepmoat-local-data -> analysis`
- 只要结构化：`report-orchestrator -> tushare-data -> deepmoat-local-data -> 12-report`
- 深度价值：`report-orchestrator -> tushare-data -> deepmoat-local-data -> value-report`
- 结构化 + 对话：`report-orchestrator -> tushare-data -> deepmoat-local-data -> 12-report -> analysis`

默认不要并行触发 `analysis + 12-report + value-report`，避免重复输出。

## 输出命名统一规范

统一目录：`outputs/reports/{symbol}_{name}/`

目录内文件命名：

`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`

约定：

- `symbol` 仅保留 6 位股票代码，不带 `.SH/.SZ`
- 统一使用下划线 `_` 分隔，不使用 `skill-` 和长连字符
- `artifact` 只在需要区分草稿/索引时追加

示例：

- `outputs/reports/000513_丽珠集团/analysis_000513_丽珠集团_2604152130.md`
- `outputs/reports/000513_丽珠集团/r12_000513_丽珠集团_2604152130.md`
- `outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130.md`
- `outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130_draft.md`
- `outputs/reports/000513_丽珠集团/index_000513_丽珠集团_2604152130.md`
