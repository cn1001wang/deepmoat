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

## 技能清单

### 投资研究（核心）

- `deepmoat-research/`：DeepMoat 投资研究唯一入口。基于投资体系 v2，整合排雷筛选 / 对话分析 / 结构化研报 / 深度估值四种模式与工作流路由。输出命名规范见仓库 `AGENTS.md`。

### 数据层

- `tushare-data/`：外部数据层（Tushare API），默认优先。
- `deepmoat-local-data/`：本地数据缓存层，仅在大批量或速度优先场景启用。

## 标准流程

| 场景 | 路由 |
|------|------|
| 排雷/筛选/观察池 | `deepmoat-local-data -> deepmoat-research(筛选模式)` |
| 对话式分析（单票） | `tushare-data -> deepmoat-research(对话模式)` |
| 结构化研报 | `tushare-data -> deepmoat-research(结构化研报模式)` |
| 深度估值/评分 | `tushare-data -> deepmoat-research(深度估值模式)` |
| 结构化 + 对话 | `tushare-data -> deepmoat-research(结构化研报) -> deepmoat-research(对话)` |
| 全流程 | `deepmoat-local-data -> deepmoat-research(筛选) -> tushare-data -> deepmoat-research(深度估值)` |
| 跟踪/监控 | `deepmoat-local-data -> deepmoat-research(筛选，比对模式)` |

默认不要并行触发多个模式，避免重复输出。

## 输出命名统一规范

详见仓库根目录 `AGENTS.md` 的"投资研究输出命名规范"章节。
