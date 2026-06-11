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

## 投资工作流

技能体系按投资决策工作流组织：**排雷 → 筛选 → 分析 → 估值 → 跟踪**

### 总控

- `workflow-orchestrator/`：工作流总控，按投资阶段做路由编排与输出命名规范。

### 数据层

- `tushare-data/`：外部数据层（Tushare API），默认优先。
- `deepmoat-local-data/`：本地数据缓存层，仅在大批量或速度优先场景启用。

### 筛选

- `stock-screener/`：排雷 + 4 种策略模板筛选 + 100 分制评分，输出观察池。

### 分析与估值

- `analysis/`：角色化对话分析（巴菲特/芒格/本杰明），不产出结构化报告。
- `12-report/`：12 模块结构化报告，不产出角色对话。
- `value-report/`：深度价值研究模板（含评分卡与终极三问）。

### 共享文档

- `shared-references/`：跨技能共享的规范文档（组合调用、输出命名、结构化模板）。

## 标准流程

| 场景 | 路由 |
|------|------|
| 排雷/筛选/观察池 | `workflow-orchestrator → deepmoat-local-data → stock-screener` |
| 对话式分析（单票） | `workflow-orchestrator → tushare-data → analysis` |
| 结构化研报 | `workflow-orchestrator → tushare-data → 12-report` |
| 深度估值/评分 | `workflow-orchestrator → tushare-data → value-report` |
| 结构化 + 对话 | `workflow-orchestrator → tushare-data → 12-report → analysis` |
| 全流程 | `workflow-orchestrator → stock-screener → tushare-data → value-report` |
| 跟踪/监控 | `workflow-orchestrator → deepmoat-local-data → stock-screener`（比对模式） |

默认不要并行触发 `analysis + 12-report + value-report`，避免重复输出。

## 输出命名统一规范

详见 `shared-references/output-naming.md`。

简要规则：
- 统一目录：`outputs/reports/{symbol}_{name}/`
- 文件名：`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`
- `symbol` 仅保留 6 位代码，不带 `.SH/.SZ`
- 统一下划线分隔

示例：
```
outputs/reports/000513_丽珠集团/analysis_000513_丽珠集团_2604152130.md
outputs/reports/000513_丽珠集团/value_000513_丽珠集团_2604152130.md
outputs/reports/screener/screener_稳健价值型_2606111430.md
```
