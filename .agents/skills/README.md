# Repo Skills

仓库内技能统一放在 `.agents/skills/`。

## Cross-Platform Local-Only Setup

为保证 Mac/Windows 一致并强制使用仓库本地 skill（不走全局 `~/.codex/skills`），在仓库根目录执行：

```bash
python scripts/ensure_repo_skills.py --purge-global
```

该命令会：

- 生成/更新 `.claude/skills`、`.trae/skills`、`.codex/skills` 到 `.agents/skills` 的本地映射。
- 清理全局目录 `~/.codex/skills` 中与本仓库同名的 skill，避免路径漂移。

## 总控与子技能

- `report-orchestrator/`：总控 skill，只做路由编排与输出命名规范。
- `analysis/`：角色化对话分析（巴菲特/芒格/本杰明），不产出 12 模块报告。
- `12-report/`：12 模式结构化报告，不产出角色对话。
- `value-report/`：深度价值研究模板（含评分卡与终极三问）。
- `deepmoat-local-data/`：读取本地数据库与本地 HTTP 接口，作为 `tushare-data` 的缓存加速层（仅在特定场景启用）。

## 标准流程

- 默认（常规单票/少量标的）：`report-orchestrator -> tushare-data -> analysis|12-report|value-report`
- 大规模横向比较（例如 20+ 标的）或用户明确要求极致速度：`report-orchestrator -> deepmoat-local-data -> analysis|12-report|value-report`
- 若使用本地缓存链路，必要时再用 `tushare-data` 对关键结论做“最新日期回补/抽样校验”。
- 结构化 + 对话：默认 `report-orchestrator -> tushare-data -> 12-report -> analysis`；极速场景可替换数据层为 `deepmoat-local-data`。

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
