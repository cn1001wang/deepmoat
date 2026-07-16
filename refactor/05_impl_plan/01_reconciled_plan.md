# DeepMoat 重构 · 合并执行计划（单一事实源）

> 版本：v1.0
> 最后更新：2026-07-16
> 定位：本文件是重构推进的**唯一执行依据**。`00_meta/MASTER_PROMPT.md` 的产品视角 P0-P5 与 `04_design/02_refactor_upgrade_design.md` 的工程视角 P0-P5 在此合并为 6 条工作轨。
> 上游：`00_meta/DECISIONS.md`（ADR-0008 确认本文件为权威）、`04_design/01_current_backend_design.md`（现状）、`04_design/02_refactor_upgrade_design.md`（工程详设）。

---

## 0. 为什么需要这份文件

`refactor/` 原有两套 P0-P5 编号，**同一代号指不同的事**：

| | P0 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| **产品视角**（MASTER_PROMPT） | 现状盘点 | Skills+投资体系工具化 | 云部署+UI | AI 报告 | Rust 切片 | Agent v2 |
| **工程视角**（04_design/02） | 地基收敛 | 读性能+缓存 | async+Repository | 公网加固 | 护城河抽核 | Rust 微服务 |

ADR-0008 决定：**以工程视角为骨架**（贴代码、可验收），产品目标作为"特性轨"挂载。两套编号都不再单独使用，统一用本文的 **Track A-G**。

---

## 1. 真实进度对账（2026-07-16 盘点）

`PROGRESS.md` 旧版声称"P0 第一步未开始"，已过期。真实状态：

### 工程轨

| 工作项 | 状态 | 证据 |
|---|---|---|
| P0① 统一响应 + 全局异常 | 🟡 半成品 | `msg->message` 已改；screener/ai_valuation 仍手写 dict，analysis 返回裸结果；无全局异常处理器 |
| P0② 统一事务边界 | ❌ 未做 | `base_bulk_upsert.py:61` 模块级 `engine.begin()`；sync.py 另有 3 处 |
| P0③ 配置加固 | 🟢 基本完成 | 去明文口令、CORS 白名单、`.env.example`；缺启动校验 |
| P0④ Alembic | ❌ 未做 | 仍 `init_db.py` `create_all` + sync.py 3 处手写 `ALTER TABLE` |
| P0⑤ 清理遗留 | ❌ 未做 | `vercel.json`/`.vercel/`/`app/stock.db`/`stock_shcemes.py` 全在 |
| P1① 在线接口不直连 Tushare | 🟢 完成 | `finance_metrics.build_metrics_table` 改只读 DB |
| P1②③ Redis 缓存 + 筛选预计算 | ❌ 未做 | 全仓无 redis |
| P2 async + Repository | ❌ 未做 | psycopg2 同步、get_db 同步、crud 未升仓储 |
| P3 公网加固 | 🟡 半成品 | Docker/systemd timer/本地脚本 done；**无鉴权/限流/推送** |
| P4 护城河引擎抽核 | ❌ 未做 | `moat_engine.py` 12 行 stub；评分逻辑散在 `screener_service.py:158` |
| P5 Rust 微服务 | ❌ 未做 | - |

### 产品轨

| 工作项 | 状态 | 备注 |
|---|---|---|
| Skills 合并 | 🟢 完成 | 合成 1 个 `deepmoat-research`（4 模式），非原计划的 3 个 → Q-0001 关闭 |
| 投资体系工具化 | ❌ 未做 | 5 个 service + 换仓决策器均未建 |
| UI 重构 | 🟡 依赖就位 | ECharts 6 + Element Plus 已是依赖；深色模式/tokens/IA 重组/移动适配均未做 → Q-0003 关闭 |
| AI 报告 v1 | ❌ 未做 | - |
| Rust 切片 | ❌ 未做 | 依赖 Track B |

---

## 2. 六条工作轨 + 依赖

```
A 地基收尾(P0剩余) ──┐
                      ├──▶ B 护城河引擎抽核(P4) ──▶ G Rust 切片(P5)
                      │        │
                      │        ▼
                      ├──▶ C 投资体系工具化(换仓决策器/组合健康度/4模式评分)
                      │
                      ├──▶ D async+仓储+缓存(P1②③/P2)   [单人低急，公网前再做]
                      │
                      └──▶ E 公网加固(鉴权/限流/推送/真云)  [移动痛点]

F UI 重构(深色/tokens/IA/移动)   [独立，依赖已就位]
```

**关键洞察**：**Track B 是最高杠杆** -- 同时是 Rust 切片（转岗故事）的前置、是 DeepMoat 核心差异化、且当前评分逻辑无权威实现与回归基线。无论优先产品价值还是转岗故事，B 都绕不开。

---

## 3. 执行优先级（13h/周约束下）

已确认起点（2026-07-16）：**提交基线 → Track A 地基收尾**。

| 顺序 | 轨 | 估时 | 产出 |
|----|----|------|------|
| 1 | 提交未提交基线 | 0.5h | clean baseline，后续重构可追溯 |
| 2 | **Track A 地基收尾** | 1-2 周 | 响应契约统一 + 事务边界 + Alembic + 清理遗留 + 启动校验 |
| 3 | **Track B 护城河抽核** | 2-3 周 | moat_engine 权威实现 + Pydantic IO + golden data |
| 4 | Track C 投资体系工具化 | 4-6 周 | 5 service + 换仓决策器 UI（依赖 B） |
| 5 | Track E 公网加固 | 2 周 | 鉴权/限流/真云/推送（移动可用） |
| 6 | Track F UI 重构 | 3-4 周 | 深色/tokens/IA/移动 |
| 7 | Track D async+缓存 | 2-3 周 | 公网压测前做 |
| 8 | Track G Rust 切片 | 10-14 周 | 转岗故事（依赖 B） |

> Track F 与 A-E 并行友好，可插周末做。Track G 周末投入，不阻塞主线。

---

## 4. Track A 地基收尾 · 任务分解（当前进行中）

按风险从低到高，每步独立可提交、保持 app 可运行：

- **A-1 清理遗留**：删 `vercel.json`/`.vercel/`/`app/stock.db`；`stock_shcemes.py` → `stock_schemas.py`（带兼容 re-export）；`fe/tsconfig.tsbuildinfo` 加入 .gitignore + `git rm --cached`。
- **A-2 config 启动校验**：pydantic validator，生产环境必填 `TUSHARE_TOKEN`/`DATABASE_URL`，CORS 禁 `*`。
- **A-3 全局异常 + 统一响应**：`main.py` 加 `add_exception_handler`；screener/ai_valuation/analysis 收敛到 `ResponseOk[T]`；路由内不再散写 `try/except`。
- **A-4 事务边界**：`bulk_upsert(table, df, conflict_cols, *, conn)` 接收外部连接；worker/service 控制事务；删模块级 `engine.begin()`（含 sync.py 3 处 `ensure_*_schema`）。
- **A-5 Alembic baseline**：引入 alembic，生成对齐 14 表的初始迁移；`alembic stamp head` 锚定现有库；`init_db.py` 退役；sync.py 手写 `ALTER TABLE` 改成迁移。

验收：响应结构全统一、`alembic upgrade head` 可重建库、`bulk_upsert` 无独立事务、遗留文件清零、生产缺 token 启动即报错。

---

## 5. 后续 Track 的入口（展开时更新本节）

- **Track B**：填实 `app/service/moat_engine.py`，收敛 `screener_service._calculate_score` + `finance_calc`(ROE/ROIC/WACC) + 持续性/量化评分；定义 `MoatInput`/`MoatScore` Pydantic schema（即 Rust 侧 serde 契约）；golden data 落 `06_tests/golden_data/`（招行/阳光/平安/茅台/宁德）。
- **Track C**：`growth_score_service` / `moat_score_service`(调 B) / `value_trap_service` / `switch_decision_service` / `portfolio_health_service`；前端 `views/switch-decision.vue`；prompts 落 `02_specs/investment_prompts.md`。
- **Track E**：API Token/JWT 中间件、slowapi 限流、推送（Q-0004 待答）、真云部署（Q-0002 待答）。
- **Track F**：`tokens.css`、深色模式、信息架构按投资体系 v2 重组、移动适配。
- **Track D**：SQLAlchemy 2.0 async + asyncpg、`crud` → `repository`、Redis 版本化缓存。
- **Track G**：`_workspace/backend/` axum + sqlx + polars，`POST /v1/moat/score`，Python HTTP 调用 + fallback，性能对比。

---

## 6. 待答问题（影响后续轨）

| 编号 | 问题 | 影响 | 状态 |
|----|------|------|------|
| Q-0002 | 云服务器选型 | Track E | open |
| Q-0004 | 推送通道 | Track E | open |
