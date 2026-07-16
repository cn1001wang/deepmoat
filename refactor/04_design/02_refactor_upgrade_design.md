# DeepMoat 后端升级迭代设计（Refactor）

> 版本：升级方案 v1.0
> 前置：`01_current_backend_design.md`（现状）、`00_meta/DECISIONS.md`（ADR-0001~0007）
> 战略锚点：ADR-0005 —— **渐进升级 Python 主体 + 护城河引擎 Rust 切片**，而非全栈重写。

---

## 0. 设计原则

本方案不推翻现有分层，而是在其上做四件事：**收敛边界、补齐缺层、抽出可移植的纯计算核、为公网移动访问加固**。所有改动可增量落地、可回滚、每步都保持 `app/` 可运行。

约束（来自 ADR）：
- 保持 Python + FastAPI 为主体，不做全量 Rust 重写（ADR-0005）。
- 数据库统一 PostgreSQL，不回退 SQLite（ADR-0002）。
- 护城河引擎是唯一被切出的 Rust 模块（ADR-0007），需与 Python 行为对齐（golden data）。
- 前端方向不变（ADR-0003），后端只需保证契约稳定与美化所需字段。

目标态：6 个月内达到「生产可用 + 移动可访问 + 自动化运行」。

---

## 1. 目标架构总览

```
                         ┌─────────────────────────────┐
                         │  客户端：Vue 前端 / 移动浏览器  │
                         └───────────────┬─────────────┘
                                         │ HTTPS (鉴权)
                          ┌──────────────▼───────────────┐
                          │  API 网关层（FastAPI）          │
                          │  统一响应 / 鉴权 / 限流 / 错误码 │
                          └──────┬───────────────┬────────┘
                                 │               │ HTTP
                    ┌────────────▼───┐   ┌───────▼────────────┐
                    │ 领域服务层       │   │ moat-engine (Rust)  │
                    │ (async)         │◄──┤ axum 微服务         │
                    │ 编排/校验/缓存   │   │ 纯计算：5维护城河评分 │
                    └────────┬────────┘   └────────────────────┘
                             │
              ┌──────────────┼───────────────┐
              ▼              ▼                ▼
      Repository 层     缓存层(Redis)     采集编排(worker)
      (async SQLA)      读缓存/幂等        调度/断点/重试
              │                                │
              └────────────┬───────────────────┘
                           ▼
                    PostgreSQL（+ Alembic 迁移）
                           ▲
                           │
                     Tushare 采集适配器（限流/重试/审计）
```

关键变化：引入鉴权与缓存层、服务层转 async、CRUD 升级为 Repository、护城河计算独立成 Rust 微服务、schema 由 Alembic 管理。

---

## 2. 分阶段迭代路线

按「先稳固地基、再补能力、最后切 Rust」排序。每阶段独立交付、可停可续。

### 阶段 P0：地基收敛（1-2 周，低风险）

目标：消除现状问题清单里的一致性与安全债，不改业务行为。

1. **统一响应契约**：所有接口统一走 `ResponseOk[T]`，`msg` 全部改 `message`；错误统一 `{code, message, data:null}`。引入全局异常处理器（`app.add_exception_handler`），路由内不再散写 `try/except`。
2. **统一事务边界**：`bulk_upsert` 改为接收 `Session`/`Connection` 参数，由调用方（worker/service）控制事务，删除模块级 `engine.begin()` 隐式事务。
3. **配置加固**：`config.py` 去掉明文默认口令，改为必填 + 启动校验；`.env.example` 落地。CORS `allow_origins` 收敛为白名单（前端域名 + 本地）。
4. **引入 Alembic**：接管建表，`init_db.py` 退役；生成初始 baseline 迁移（对齐现有 14 表）。
5. **清理遗留**：删除 `app/stock.db`、`vercel.json`/`.vercel`（与常驻 worker 不匹配）；`stock_shcemes.py` 重命名为 `stock_schemas.py`（加兼容 re-export，前端无感）。

验收：接口响应结构一致、`alembic upgrade head` 可重建库、CORS 白名单生效。

### 阶段 P1：读性能与缓存（1-2 周）

目标：接口时延与 Tushare 解耦，支撑移动端弱网。

1. **在线接口只读 DB，不直连 Tushare**：`finance_metrics.build_metrics_table` 拆成 `build_from_db`（在线，纯读 PG）与采集路径（离线）。Tushare 调用全部收敛到 worker/采集适配器。
2. **引入 Redis 读缓存**：财务表、趋势、筛选结果按 `(ts_code, years, 数据版本)` 缓存，TTL + 同步完成后主动失效。缓存 key 带 `sync_log` 的最新 end_date 做版本位，天然幂等。
3. **筛选预计算**：`run_screener` 全表遍历改为「离线物化候选池 + 在线按参数过滤」。用 PG 物化视图或结果表存每股票的 avg_roe/负债率/现金含量等派生指标，在线只做阈值筛选与打分。

验收：`/finance/table`、`/screener/run` P95 时延显著下降且不受 Tushare 限流影响。

### 阶段 P2：async 化与 Repository（2-3 周）

目标：消除 async def 路由跑同步 DB 的阻塞，规整数据访问。

1. **SQLAlchemy 2.0 async**：`session.py` 引入 `create_async_engine` + `AsyncSession`，`get_db` 改 async 依赖；DB 驱动换 `asyncpg`。
2. **CRUD → Repository**：`crud_*` 收敛为 `repository/` 下按聚合根组织的仓储类（`FinanceRepository`、`StockRepository`、`ScreenerRepository`），统一 `AsyncSession` 入参，消除散落的 `db.query(...)`。
3. **服务层 async 编排**：`ai_service` 已是 async，其余 service 逐个转 async，IO 让出事件循环。

验收：并发压测下事件循环不被 DB 查询阻塞；仓储层单测覆盖主查询。

### 阶段 P3：公网移动访问加固（2 周，用户核心痛点）

目标：从「单人内网」升级为「可安全公网移动访问」。

1. **鉴权**：单用户场景用 API Token / 简单 JWT 中间件即可，路由按需 `Depends(auth)`。
2. **限流**：接入 slowapi 或网关层限流，防外呼 AI 与筛选被刷。
3. **AI 报告推送**：结合 OPEN_QUESTIONS Q-0004，AI 估值生成后推微信（server 酱）+ 邮件归档。
4. **部署形态**：常驻服务（uvicorn + gunicorn/uvicorn workers）+ 定时同步（cron/systemd timer 调 `worker.sync`），部署到云主机（Q-0002 待定，倾向 Hetzner/阿里云香港 + Cloudflare）。docker compose 起 app + PG + Redis。

验收：手机浏览器可登录访问、AI 报告能推送到手机、定时同步自动跑。

### 阶段 P4：护城河引擎抽核（2 周，为 Rust 切片铺路）

目标：把散落的护城河/评分逻辑收敛成**纯函数计算核**，先在 Python 内落地权威实现。

1. **统一计算入口**：填实 `moat_engine.py`，把 `screener_service._calculate_score`、`finance_calc`（ROE/ROIC/WACC）、持续性与量化评分统一进 `MoatEngine`。输入=财务三表 DataFrame/结构化对象，输出=评分对象，**无副作用、不碰 DB**（呼应 ADR-0007 边界）。
2. **契约固化**：定义引擎输入/输出的 Pydantic schema（后续即 Rust 侧 serde 契约）。
3. **金标准数据**：选一批代表性股票，落 `06_tests/` golden data，作为 Python↔Rust 行为一致性基线。

验收：护城河评分有单一权威实现 + 回归金标准，筛选与报告都调它。

### 阶段 P5：Rust 护城河微服务（周末投入，转岗故事载体）

目标：ADR-0007 的 Rust 切片，独立可演示。

1. **服务形态**：`refactor/_workspace/backend/` 下 axum 服务，`POST /moat/score` 接收三表 JSON，返回评分。用 polars（ADR-0004）做数值计算。
2. **集成方式**：Python 服务层通过 HTTP 调用 Rust 引擎（清晰语言边界），失败回退 Python 实现（双实现并存期）。
3. **一致性保证**：Rust 跑 P4 的 golden data，与 Python 输出逐字段比对，容差内即通过。
4. **性能对比**：批量算 5000 只票，实测 Python vs Rust 时延，产出可讲的性能数据。

验收：Rust 引擎与 Python 结果一致、批量性能有量化优势、可独立部署演示。

---

## 3. 目标目录结构（Python 主体）

```
app/
├── main.py                 # app 装配、中间件、异常处理、路由注册
├── config.py               # 必填校验 + 分环境
├── core/                   # 新增：鉴权、限流、缓存客户端、异常、日志
│   ├── security.py
│   ├── cache.py            # Redis 封装 + 版本化 key
│   ├── exceptions.py       # 统一错误码与处理器
│   └── deps.py             # get_db / auth 等依赖
├── db/
│   ├── session.py          # async engine + AsyncSession
│   └── migrations/         # Alembic
├── models/                 # ORM（清理拼写、去 SQLite）
├── repository/             # 原 crud/ 升级：按聚合根组织的 async 仓储
├── service/
│   ├── moat_engine.py      # 纯计算核（P4）+ Rust 客户端适配（P5）
│   ├── finance_metrics.py  # 只读 DB，产出加工表
│   ├── screener_service.py # 在线过滤 + 打分（依赖物化派生指标）
│   ├── trend_service.py
│   └── ai_service.py       # + 推送
├── schemas/                # 统一命名，含 moat 引擎 IO 契约
├── api/v1/                 # 统一响应契约 + 鉴权
├── worker/                 # 采集编排：限流/重试/断点/审计（唯一 Tushare 出口）
└── utils/
```

---

## 4. 横切关注点设计

**统一响应与错误码**：`ResponseOk[T]` 为唯一出参；错误码集中在 `core/exceptions.py`（如 4040 数据缺失、5030 上游 Tushare 不可用、5031 AI 超时），全局 handler 兜底。

**缓存版本化**：缓存 key = `f"finance:{ts_code}:{years}:{max_end_date}"`，`max_end_date` 取自 `FinanceSyncLog`。同步完成即让老版本自然过期，无需手动清缓存，避免脏读。

**采集健壮性**：worker 层为每个 Tushare 接口保留 `RateLimiter`，补重试（指数退避）+ 采集审计（每次同步写入 run 记录：起止、成功/失败股票数、断点），失败可续跑。

**可观测性**：结构化日志（沿用 `ai_service` 的 logger 风格推广到全局）、请求耗时中间件、同步任务指标（成功率/耗时/覆盖率）。

**测试策略**：护城河/筛选/指标计算走 golden data 回归（`06_tests/`）；仓储层用测试 PG（docker）跑集成测试；API 层用 `httpx.AsyncClient` + FastAPI TestClient 冒烟。

---

## 5. 迁移风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| async 化引入并发 bug | 数据竞争/连接泄漏 | 分模块灰度，保留同步分支对照；连接池上限 + 超时 |
| Alembic baseline 与现库不一致 | 迁移失败 | 先 `--autogenerate` diff 校对，空迁移锚定现状再演进 |
| 缓存脏读 | 展示旧财报 | 版本化 key 绑定 `sync_log`，不做手动失效 |
| Rust 引擎行为不一致 | 评分错误 | golden data 逐字段比对 + Python 兜底回退 |
| 公网暴露安全 | 数据泄露/被刷 | 鉴权 + 限流 + CORS 白名单 + 云安全组仅放 443 |
| 单人时间有限（13h/周） | 排期滑落 | P0-P3 保证主线可用，P4/P5 放周末、不阻塞日常投资使用 |

---

## 6. 阶段-价值映射

| 阶段 | 解决的现状问题 | 用户价值 |
|------|----------------|----------|
| P0 | 契约/事务/CORS/迁移/遗留 | 工程整洁、可维护、生产安全基线 |
| P1 | 直连 Tushare、无缓存、全表遍历 | 接口快、弱网可用、筛选秒回 |
| P2 | 同步 DB 阻塞、CRUD 散乱 | 并发稳、数据层清晰可测 |
| P3 | 无鉴权/限流/推送、部署形态 | **移动可访问 + 自动化运行**（核心痛点） |
| P4 | 护城河逻辑散落、无金标准 | 权威可信的护城河评分 + 回归保障 |
| P5 | —— | Rust 转岗故事（架构+实现+性能数据） |

---

## 7. 首个可执行切口（本周即可动手）

建议从 P0 起步，风险最低、收益立现：
1. 建全局异常处理器 + 统一 `ResponseOk`，改掉 screener/ai 的 `msg`。
2. `bulk_upsert` 加 `conn` 参数，worker 侧传入事务。
3. `config.py` 去明文口令 + CORS 白名单 + `.env.example`。
4. 接 Alembic，生成 baseline。

这四步不改业务行为、可独立提交，完成后即进入 P1 的缓存与读写分离。
