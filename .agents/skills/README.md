# Repo Skills

仓库内的 prompt/agent 说明统一收敛到 `skills/`。

- `skills/analysis/`：角色化对话分析（巴菲特/芒格/本杰明），不生成结构化报告。
- `skills/12-report/`：12 模式结构化报告，不生成角色对话。
- `skills/value-report/`：更深度的价值研究模板（评分卡、终极三问等）。
- `skills/deepmoat-local-data/`：读取项目数据库和本地 HTTP 接口，作为外部 `tushare-data` 的本地口径补充。

推荐组合：

- 只要对话：`tushare-data -> deepmoat-local-data -> analysis`
- 只要结构化：`tushare-data -> deepmoat-local-data -> 12-report`
- 结构化 + 对话：`tushare-data -> deepmoat-local-data -> 12-report -> analysis`
- 深度价值模板：`tushare-data -> deepmoat-local-data -> value-report`

默认不要并行同时触发 `analysis + 12-report + value-report`，避免冗余与重复输出。
