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

`outputs/` 下所有报告文件统一为：

`skill-{skill_name}--{ts_code}--{name}--{YYYYMMDD-HHmm}--{artifact}.md`

示例：

- `skill-analysis--000513-SZ--丽珠集团--20260415-2130--dialogue.md`
- `skill-12-report--000513-SZ--丽珠集团--20260415-2130--report.md`
- `skill-value-report--000513-SZ--丽珠集团--20260415-2130--report.md`
- `skill-report-orchestrator--000513-SZ--丽珠集团--20260415-2130--index.md`
