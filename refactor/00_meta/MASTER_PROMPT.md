# DeepMoat 重构 · 主控提示词（自驱 Agent 入口）

> 启动方式：把 "## 主控提示词正文" 整段 copy 给一个长跑的 Claude（或 Workflow 的根 agent）。
> 续跑方式：直接 `cat refactor/00_meta/MASTER_PROMPT.md` 再贴给 agent，它会自己读 PROGRESS.md 接着干。

---

## 项目锚点（已拍板，不要再改）

- **后端语言**：Rust
- **Web 框架**：`axum`（不要换 actix-web / poem）
- **数据库**：PostgreSQL（现状已是 PG；不再回退 SQLite）
- **数据访问**：`sqlx`（编译期校验 SQL）+ `deadpool-postgres` 备选连接池
- **数值计算 / DataFrame**：`polars`（替代 pandas）
- **异步运行时**：`tokio`
- **OpenAPI**：`utoipa` + `utoipa-swagger-ui`
- **日志**：`tracing` + `tracing-subscriber`
- **配置**：`figment` + 环境变量
- **错误处理**：lib 层 `thiserror`，bin 层 `anyhow`
- **前端方向**：保留现有 Vue 3 + Vite 技术栈，**不切框架**；只做 UI 美化（UI 库升级、设计 token、深色模式、图表用 ECharts）。fe/ 现有代码作为基线，重设计稿 + 增量改造方案放 `refactor/04_design/frontend_redesign.md`，PoC 落 `refactor/_workspace/frontend/`。

---

## 不变约束（违反即停下，写到 OPEN_QUESTIONS.md）

1. 工作根目录：`C:\codes\github\deepmoat`
2. **只读区**：`app/`、`fe/`、`scripts/`、`README.md`、`AGENTS.md`、`Clippings/`、`obsidian/`、`outputs/`、`outputs_old/`、`tests/`、`pyproject.toml`、`uv.lock`、`vercel.json`、`Users/`、根目录的中文 md 笔记
3. **可写区**：`refactor/` 下全部内容（含 `refactor/_workspace/` 内 Rust / 前端 PoC 代码）
4. 任何对 `app/` 或 `fe/` 的修改诉求 → 先写进 `refactor/00_meta/OPEN_QUESTIONS.md`，**不要直接动手**
5. 涉及外部网络（Tushare、AI API）只在测试阶段用 mock；**禁止**把真实 token / API key 写进任何文档或代码（`.env` 不进 refactor/）
6. 每完成一个任务：① 更新 `PROGRESS.md` ② 在 `DECISIONS.md` 追加决策 ③ 提交 git，消息格式 `refactor(P{阶段号}): {任务摘要}`
7. 单次 Read 不超过 1500 行；先用 Glob/Grep 定位，再读局部
8. 所有产出文档**中文**；代码注释中英文混用按既有风格
9. 每写一个 Mermaid 图先在脑内过语法，避免渲染失败

---

## 阶段编号与门禁（DoD = Definition of Done）

| 阶段 | 名称 | 主要产物 | DoD 摘要 |
|------|------|----------|----------|
| P1 | 现状盘点 | inventory_app.md / inventory_fe.md / data_model.md / routes.md / frontend_routes.md | 5 个文件齐全；ER 图能渲染；路由清单字段齐 |
| P2 | 业务规格 | PRD.md / feature_spec.md / glossary.md | PRD 含北极星指标；功能说明书每模块状态明确 |
| P3 | 接口契约 | openapi.yaml / api_reference.md / error_codes.md | `npx @redocly/cli lint` 0 error |
| P4 | 架构详设 | architecture.md / rust_modules.md / detailed_design.md / frontend_redesign.md | C4 三视图齐；crate 划分明确；护城河引擎伪代码可读 |
| P5 | 实施计划 | milestones.md / task_breakdown.md | 任务粒度 ≤1 天 |
| P6 | Rust 骨架 | _workspace/backend/ | 健康检查 + 1 个端点 + 1 个指标对齐 Python |
| P7 | 前端美化 PoC | _workspace/frontend/ + design tokens | Home + StockCard 两页跑通 |
| P8 | 测试方案 | test_strategy.md / test_cases.md / golden_data/ | 每接口 ≥3 例；金标准覆盖 ≥5 只票 |
| P9 | 自测回归 | test_report.md | golden_data 差异 ≤1e-6 |

---

## 工作循环（每一轮严格执行）

1. 读 `refactor/00_meta/PROGRESS.md`，确认当前阶段与下一项任务编号
2. 检查 `OPEN_QUESTIONS.md`：如果阻塞当前任务，跳到下一不阻塞任务；若全阻塞则进入待命态并输出汇总
3. 执行任务（读源 → 写文档 / 写代码 / 写测试）
4. 过自检清单
5. 更新 PROGRESS.md（in_progress / done 都要标，不要只标 done）
6. `git add refactor/ && git commit -m "refactor(P{n}): {摘要}"`
7. 进入下一轮

## 自检清单（每轮必过）

- [ ] 没有改动只读区
- [ ] 新文档顶部写了：DoD、最后更新时间、依赖的上游文档
- [ ] 用了 Mermaid 的图过语法检查
- [ ] 关键决定已写进 DECISIONS.md（上下文/选项/决策/后果）
- [ ] PROGRESS.md 反映真实状态
- [ ] 卡住的事进了 OPEN_QUESTIONS.md（不硬猜）
- [ ] 没有泄露真实 token / 数据库密码

## 卡死兜底

- 同一任务连续失败 3 次 → 写 OPEN_QUESTIONS.md，跳过
- 连续两阶段无新进展 → 暂停所有任务，输出"待人工决策"汇总，进入待命态

---

## 阶段任务库

### P1 现状盘点
- T1.1 列出 `app/` 全部 Python 模块清单 → `01_discovery/inventory_app.md`
- T1.2 列出 `fe/` 清单 → `01_discovery/inventory_fe.md`
- T1.3 抽 `app/models/models.py` SQLAlchemy 表结构，画 ER 图 → `01_discovery/data_model.md`
- T1.4 抽 `app/api/v1/` FastAPI 路由 → `01_discovery/routes.md`
- T1.5 抽 `fe/src/router` × `views` → `01_discovery/frontend_routes.md`

清单表格统一格式：
`| 路径 | 类型 | 一句话职责 | 关键符号 | 外部依赖 | 风险/坏味 |`
不复制源码，只抽签名和职责。文件末尾追加 "下一阶段需要继承的关键事实"。

### P2 业务规格
- T2.1 `02_specs/PRD.md`：定位 / 3 类用户画像 / 核心场景用户故事 / 范围内外 / 北极星指标 / 非功能需求
- T2.2 `02_specs/feature_spec.md`：按模块（选股 / 护城河评级 / 财务三表 / AI 估值 / 行业看板 / 数据同步）写：输入、输出、业务规则、边界、当前实现状态（已实现/部分/未实现/TBD@P2）
- T2.3 `02_specs/glossary.md`：护城河、ROIC、WACC、自由现金流、宽/窄护城河等

### P3 接口契约
- T3.1 `03_api/openapi.yaml`（OpenAPI 3.1）
  - 路径前缀 `/api/v1`
  - 统一错误：`{ code, message, details? }`
  - 统一分页：`{ items, total, page, page_size }`
  - 时间 ISO8601 + UTC；金额字段名带单位后缀（`_cny` / `_yi` / `_pct`）
  - 每个 schema 必填 description + example
- T3.2 `03_api/api_reference.md`：人读版，每接口配请求/响应示例
- T3.3 `03_api/error_codes.md`
- DoD：`npx @redocly/cli lint openapi.yaml` 0 error

### P4 架构详设
- T4.1 `04_design/architecture.md`：C4 上下文 / 容器 / 组件三视图（Mermaid）+ 部署图（含 PG）
- T4.2 `04_design/rust_modules.md`：crate 划分
  - `deepmoat-api`：axum 路由 + utoipa
  - `deepmoat-core`：领域类型、错误、配置
  - `deepmoat-data`：sqlx + repo trait + PG 迁移
  - `deepmoat-moat`：护城河引擎、财务指标
  - `deepmoat-worker`：Tushare 同步任务
  - `deepmoat-ai`：AI 估值适配器（trait 化，多 provider）
  - `deepmoat-cli`：等价旧 `python -m app.worker.sync` 的 CLI
- T4.3 `04_design/detailed_design.md`：护城河引擎、财务指标计算、Tushare 增量 / 全量同步、AI 估值适配器，逐一伪代码 + 数据流 + 异常路径
- T4.4 `04_design/frontend_redesign.md`：信息架构、视觉风格（深色模式 + 中式留白）、UI 库选型对比（Naive UI vs Element Plus vs Ant Design Vue，给推荐）、关键页面线框（Mermaid 或 ASCII）、design token 草表

### P5 实施计划
- T5.1 `05_impl_plan/milestones.md`：M0 准备 / M1 数据层 / M2 核心引擎 / M3 API / M4 worker / M5 前端美化 / M6 切流
- T5.2 `05_impl_plan/task_breakdown.md`：每里程碑拆到 0.5~1 天

### P6 Rust 骨架（在 `refactor/_workspace/backend/`）
- T6.1 `cargo new --workspace` 起 workspace；按 rust_modules.md 拉 crate
- T6.2 `deepmoat-api`：`/health` + `/openapi.json` + Swagger UI
- T6.3 `deepmoat-data`：sqlx 连 PG，跑通最简 query（`SELECT 1`）
- T6.4 `deepmoat-moat`：移植 ROIC 1 个指标作 PoC；与 Python 对齐
- T6.5 跑通 `GET /api/v1/stocks/{ts_code}` 1 个端点

强约束：
- 不污染仓库根；workspace 在 `refactor/_workspace/backend/`
- thiserror（lib）+ anyhow（bin）分层
- IO 用 tokio；阻塞计算 spawn_blocking
- 配置走 figment + env，禁硬编码
- 每移植 1 个 Python 算法 → 同 PR 加 1 条 golden_data 对照测试
- 每 commit `cargo fmt && cargo clippy -- -D warnings` 必过

### P7 前端美化 PoC（在 `refactor/_workspace/frontend/`）
- T7.1 复制现 `fe/` 为基础（不动原 fe/），抽 design tokens 文件 `tokens.css`
- T7.2 引入推荐 UI 库（P4 决策）+ ECharts；保留 UnoCSS
- T7.3 重设计 Home + StockCard 两页；加深色模式切换
- T7.4 不重写 API 层，只重做 UI 层

### P8 测试方案
- T8.1 `06_tests/test_strategy.md`：单元 / 集成 / 契约 / E2E 四层
- T8.2 `06_tests/test_cases.md`：每接口 ≥3 例（正常/边界/异常）
- T8.3 `06_tests/golden_data/`：用旧 Python 跑典型股票（招商银行 600036 / 阳光电源 300274 / 平安银行 000001 / 贵州茅台 600519 / 宁德时代 300750）的指标输出存 JSON

### P9 自测与回归
- T9.1 `cargo test --all` 跑通
- T9.2 用 golden_data 做契约对齐，差异 >1e-6 标红入 `test_report.md`
- T9.3 出 `test_report.md`：通过率 / 失败用例 / 性能基线对比

---

## 启动指令（agent 第一次执行时）

1. 读本文件全文
2. 读 `PROGRESS.md` 确认起点（首次为空 → 从 P1.T1.1 开始）
3. 进入工作循环
