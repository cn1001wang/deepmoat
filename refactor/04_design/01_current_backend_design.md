# DeepMoat 后端（app/）详细设计文档

> 版本：现状盘点 v1.0
> 范围：`app/` FastAPI 后端全量
> 定位：个人长期价值投资分析工具的服务端。数据源为 Tushare，落库 PostgreSQL，对外提供财务数据、趋势、筛选、AI 估值等 HTTP 接口，供 Vue 前端（`fe/`）与脚本（`scripts/`）消费。

---

## 1. 系统概览

DeepMoat 后端是一个典型的分层式 FastAPI 应用，核心职责分三块：

1. **数据采集（离线）**：`app/worker/sync.py` 通过命令行调度，从 Tushare 拉取股票列表、公司信息、财务三表、财务指标、分红、审计意见、主营构成、日线指标，写入 PostgreSQL。
2. **数据加工（在线/离线混合）**：`app/service/` 层把原始三表加工为护城河指标、趋势序列、筛选结果、AI 估值上下文。
3. **数据服务（在线）**：`app/api/v1/` 暴露 REST 接口，前端与脚本调用。

技术栈：Python 3.13、FastAPI、SQLAlchemy 2.0（ORM，非 async）、Pandas、Tushare SDK、httpx（调用外部 AI）、Pydantic v2 + pydantic-settings、uv 管理依赖。

```
Tushare API ──> worker/sync.py ──> CRUD(bulk_upsert) ──> PostgreSQL
                                                            │
                                        ┌───────────────────┤
                                        ▼                   ▼
                              service(计算/加工)      crud(读查询)
                                        │                   │
                                        └────────┬──────────┘
                                                 ▼
                                        api/v1 (FastAPI 路由)
                                                 │
                                                 ▼
                                    Vue 前端 fe/ + scripts/ + AI
```

---

## 2. 分层架构

分层自底向上，依赖方向单向（上层依赖下层，下层不反向依赖上层）：

| 层 | 目录 | 职责 | 关键文件 |
|----|------|------|----------|
| 配置 | `app/config.py` | 环境变量集中管理（DB、Tushare token、AI 参数） | `config.py` |
| 持久化基础 | `app/db/` | Engine、Session 工厂、`get_db` 依赖注入、declarative `Base` | `session.py` |
| 领域模型 | `app/models/` | SQLAlchemy ORM 表定义 + `to_dict()` | `models.py` |
| 数据访问 | `app/crud/` | 单表读写、批量 upsert、断点查询 | `crud_*.py`、`base_bulk_upsert.py` |
| 领域服务 | `app/service/` | 财务指标计算、趋势、筛选、护城河引擎、AI 估值、Tushare 适配 | `finance_metrics.py` 等 |
| 接口 | `app/api/v1/` | FastAPI 路由，参数校验、响应封装、异常映射 | `analysis.py` 等 |
| 响应契约 | `app/schemas/` | Pydantic 响应/请求模型 | `*_schemes.py` |
| 工具 | `app/utils/` | DataFrame 清洗、日期、限流、统一响应包装 | `*.py` |
| 离线任务 | `app/worker/` | 命令行数据同步调度 | `sync.py` |
| 入口 | `app/main.py` | FastAPI app、CORS、路由注册、uvicorn 启动 | `main.py` |

---

## 3. 各层详解

### 3.1 入口层 `app/main.py`

- 创建 `FastAPI(title=settings.PROJECT_NAME)`。
- 挂 `CORSMiddleware`，当前 `allow_origins=["*"]`（开发态放开，生产需收敛）。
- 注册五个路由，统一前缀 `/api`：`analysis`、`raw_data`、`user_data`、`ai_valuation`、`screener`。
- `__main__` 下用 uvicorn 起服务，端口取环境变量 `PORT`（默认 5005），`reload=True`。

### 3.2 配置层 `app/config.py`

- `Settings(BaseSettings)`，从 `.env` 读取：`DATABASE_URL`、`TUSHARE_TOKEN`、`PROJECT_NAME`、`AI_API_URL/KEY/MODEL`。
- 单例 `settings` 全局导入。默认 `DATABASE_URL` 指向本地 PG。

### 3.3 持久化层 `app/db/session.py`

- 同步 `create_engine`，`sessionmaker`（`autoflush=False, autocommit=False`）。
- `Base = declarative_base()`，所有模型继承。
- `get_db()` 生成器依赖，`try/finally` 关闭 session；FastAPI 路由通过 `Depends(get_db)` 注入。
- 注意：`bulk_upsert` 里直接用模块级 `engine.begin()` 独立事务，绕过请求级 session。

### 3.4 模型层 `app/models/models.py`

共 14 张表，全部继承 `Base`，大多带 `to_dict()`（返回驼峰命名 dict，服务前端）：

- 基础维度：`SwIndustry`（申万行业）、`IndexMember`（指数成分）、`StockBasic`（股票列表）、`StockCompany`（公司信息）。
- 财务三表：`Income`（利润表）、`BalanceSheet`（资产负债表）、`CashFlow`（现金流量表）。
- 衍生财务：`FinaIndicator`（财务指标，ROE/负债率等）、`FinaMainbz`（主营构成）、`FinaAudit`（审计意见）、`Dividend`（分红送股）。
- 行情：`DailyBasic`（每日基础指标：PE/PB/股息率/市值）。
- 同步元数据：`FinanceSyncLog`（每股票每表的同步断点 end_date）。
- 用户态：`UserStockData`（备注 remark + 逗号分隔 tags）。

主键约定：多为 `ts_code`（+ `end_date`/`index_code`）联合主键，配合 `bulk_upsert` 的 `ON CONFLICT`。

### 3.5 数据访问层 `app/crud/`

- 每张业务表一个 `crud_*.py`，提供 `save_*_bulk` / `get_*` / `check_*_exists`。
- `base_bulk_upsert.bulk_upsert(table, df, conflict_cols)` 是写入核心：
  1. 只保留表中真实存在的列；
  2. 丢弃冲突键含空值的行；
  3. 批次内按冲突键去重（保留最后一条）；
  4. `NaN → None`；
  5. PG `insert().on_conflict_do_update()`，更新除冲突键外的所有列；
  6. 独立 `engine.begin()` 事务执行。
- `crud_sync_log` 提供 `get_db_max_end_date` / `update_sync_log`，支撑增量同步断点。
- `crud_trend` 提供趋势查询：`get_financial_history`、`get_comparable_period_data`（去年同期）。

### 3.6 领域服务层 `app/service/`

- `tushare_service.py`：Tushare 唯一适配层。`_get_tushare_pro()` 避免 `ts.set_token()` 写本地缓存文件（沙箱兼容）。为三表各建 `RateLimiter(180/60s)`。封装 `get_income_all`、`get_stock_list`、`fetch_fina_indicator`、`fetch_dividend`、`fetch_fina_mainbz` 等。
- `finance_service.py`：财务三表同步编排。`TABLES` 映射 `{表名: (fetch, save)}`；`fetch_finance_for_stock*` 做「全量拉取 → 内存去重/增量过滤 → 只入新期或 `update_flag=1` 更正 → 更新断点」。含 `_2`、`_overwrite` 变体。
- `finance_metrics.py`：核心指标计算（约 540 行）。`build_metrics_table(ts_code, years)` 从 Tushare/DB 取三表 + 指标 + 分红，用 Pandas `merge_frames`/`ensure_columns`/`filter_periods` 对齐周期，算 YoY、毛利率、现金流类型标记等，输出 `{periods, rows}` 供 `/finance/table` 接口。
- `trend_service.py`：为前端 sparkline 生成近 8 季度趋势（收入/扣非/净利/景气度），逐期查去年同期算 YoY。
- `screener_service.py`：策略筛选。`STRATEGY_DEFAULTS` 内置四策略（稳健价值 / 高质量成长 / 高股息低估值 / 困境反转）。`run_screener` 遍历全部上市股票，过滤 ST、按 ROE/负债率（含金融地产豁免）/经营现金流/现金含量筛选并 `_calculate_score` 打分；`check_risk` 做单票排雷。
- `moat_engine.py`：护城河引擎，**当前为占位骨架**（`build_metrics_table` 只有 return 空 dict 的桩），是后续 Rust 切片的目标模块。
- `finance_calc.py`：空文件（ROE/ROIC/WACC 预留）。
- `ai_service.py`：AI 估值。`_build_financial_context` 拼近 N 年年报摘要，`generate_valuation` 用 httpx 异步调外部 AI（`AI_API_URL`），`save_valuation_report` 落盘报告到 `outputs/reports/`。

### 3.7 接口层 `app/api/v1/`

统一前缀 `/api`，响应用 `utils/api_utils.ok()` 或 `ResponseOk[T]` 泛型包装（`{code, message, data}`）。

| 路由文件 | 前缀 | 端点 | 说明 |
|----------|------|------|------|
| `analysis.py` | `/analysis` | `GET /trends/{ts_code}`、`GET /indicators/{ts_code}` | 趋势序列、详细指标 |
| `raw_data.py` | (无) | `GET /finance/table`、`/annual_metric_trends`、`/finance/card`、`/sw_industry`、`/stock_basic[_all]`、`/index_member[_by_ts_code]`、`/company`、`/fina_indicator`、`/fina_audit`、`/daily_basic` | 原始/加工财务与基础数据，最大文件（约 780 行） |
| `screener.py` | `/screener` | `POST /run`、`GET /risk-check` | 策略筛选、单票排雷 |
| `ai_valuation.py` | `/ai` | `POST /valuation`、`POST /valuation/save` | AI 估值生成与落盘 |
| `user_data.py` | (无) | `GET/POST /user_data/{ts_code}`、`GET /user_data_all`、`GET /tags/history` | 用户备注与标签 |

异常处理：路由内 `try/except` 转 `HTTPException`（500），空数据转 404。

### 3.8 契约层 `app/schemas/`

- Pydantic v2 模型，`model_config = {"from_attributes": True}`（ORM 模式）。
- 覆盖 `StockBasicRead`、`FinaIndicatorRead`、`DailyBasicRead`、`MetricsTable`、`UserStockDataRead/Update` 等。
- 命名遗留问题：`stock_shcemes.py`（拼写错误 schemes→shcemes）。

### 3.9 工具层 `app/utils/`

- `api_utils.py`：`ok()` + `ResponseOk` 泛型响应。
- `df_utils.py`：`dedup_finance_df` 财报去重。
- `finance_df.py`：`ensure_columns` / `merge_frames` / `filter_periods` / `safe_div` / `yoy` / `to_billion` / `format_percent` 等纯计算辅助。
- `date_utils.py`：`generate_periods` 生成报告期序列。
- `tushare_utils.py`：`RateLimiter` 限流器、`fetch_paginated` 分页抓取。

### 3.10 离线任务层 `app/worker/sync.py`

- argparse 驱动，约 790 行。各数据域一个开关：`--industry` `--stock_basic` `--stock_company` `--index_member` `--finance` `--daily` `--fina_indicator` `--dividend` `--fina_audit` `--fina_mainbz`。
- `--workers` 控制 `ThreadPoolExecutor` 并发；`--finance_overwrite` 全覆盖重拉；`--daily_hybrid` 近年逐日+历史月末抽样；`--fina_mainbz_force` 强刷。
- `get_db_session()` 上下文管理器统一 commit/rollback/close。

---

## 4. 关键数据流

### 4.1 数据同步（离线）

```
CLI(--finance) → sync.py 遍历 StockBasic
  → finance_service.fetch_finance_for_stock_2(ts_code)
    → tushare_service.get_income_all/... (RateLimiter 限流分页)
    → df_utils.dedup_finance_df 去重
    → crud_sync_log 读断点，过滤增量
    → crud_*.save_*_bulk → bulk_upsert(ON CONFLICT)
    → crud_sync_log.update_sync_log 更新断点
```

### 4.2 财务表查询（在线）

```
GET /api/finance/table?ts_code&years
  → build_metrics_table (finance_metrics)
    → 取三表+指标+分红 → Pandas 对齐周期 → 算 YoY/毛利/现金流类型
  → ResponseOk[MetricsTable]
```

### 4.3 策略筛选（在线）

```
POST /api/screener/run {strategy, params, years}
  → run_screener 遍历全部上市股 → 多维过滤 + 打分
  → {code, data:[排序候选池], msg}
```

### 4.4 AI 估值（在线，异步外呼）

```
POST /api/ai/valuation {ts_code}
  → _build_financial_context 拼上下文
  → httpx 异步调 AI_API_URL
  → 返回估值文本；POST /ai/valuation/save 落盘 outputs/reports/
```

---

## 5. 现状问题清单（供重构参考）

按影响面排列：

1. **数据库会话双通道**：请求走 `get_db` session，`bulk_upsert` 走模块级 `engine.begin()`，事务边界不统一，批量写与请求内读写无法共享事务。
2. **同步引擎为 stub**：`moat_engine.py`、`finance_calc.py` 是空/桩，护城河评分逻辑实际散落在 `screener_service`、`finance_metrics`，缺少单一权威计算入口。
3. **在线接口直连 Tushare**：`finance_metrics.build_metrics_table` 在请求路径里可能触发 Tushare 网络调用，接口时延与外部限流耦合，无缓存层。
4. **响应契约不统一**：部分接口用 `ResponseOk[T]`（`{code,message,data}`），部分手写 `{code, data, msg}`（screener/ai），字段名 `message` vs `msg` 不一致。
5. **CORS 全开**：`allow_origins=["*"]` + `allow_credentials=True` 生产不安全。
6. **命名/拼写债**：`stock_shcemes.py`、`ennname`、混用中英文文件名，`fetch_finance_for_stock` 与 `_2`/`_overwrite` 多变体并存。
7. **无迁移工具**：建表靠 `Base.metadata.create_all`（`init_db.py`），schema 演进无 Alembic 版本管理。
8. **无鉴权/限流/审计**：接口裸奔，适合单人内网，不适合公网移动访问（这是用户明确痛点之一）。
9. **无异步 IO**：SQLAlchemy 同步 + 部分 async 路由混用，`get_db` 是同步 session，async def 路由里跑同步 DB 查询会阻塞事件循环。
10. **缺测试与金标准**：`tests/` 稀疏，护城河/筛选计算无回归基线。
11. **配置默认值含明文口令**：`config.py` 默认 `DATABASE_URL` 带 `postgres:123456`。
12. **SQLite 遗留**：`app/stock.db` 与 PG 并存，ADR-0002 已决策统一 PG，代码里仍有残留。

---

## 6. 部署与运行现状

- 依赖：`uv sync`（`pyproject.toml`，requires-python ≥3.13）。
- 建表：`uv run python -m app.scripts.init_db`。
- 起服务：`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`。
- 同步：`uv run python -m app.worker.sync --finance --workers 1` 等。
- 部署残留：`vercel.json` / `.vercel`（Serverless 尝试），与常驻同步 worker 模型不匹配。
