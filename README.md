# DeepMoat - 深度护城河价值选取器

> **“知价值之本，行投资之真。”**
> 
> DeepMoat 是一款基于 **FastAPI** 和 **阳明心学** 哲学构建的高性能基本面分析工具。它借鉴 **Morningstar (晨星)** 的护城河评级逻辑，利用 **Tushare** 财经数据，帮助投资者在浩瀚星空中定位具有深度竞争壁垒的价值标的。

---

DeepMoat 认为，数据不只是数字，而是企业经营的“良知”体现。

- 格物：深度清洗 财报 每一行原始数据。

- 致知：通过 ROIC > WACC 等指标提炼核心价值。

- 诚意：排除虚假利润，回归现金流本质。

---

## 🌟 核心特性

* **知行合一 (Unity of Knowing & Acting)**：拒绝短线情绪，基于严密的财务逻辑（ROIC、自由现金流等）进行选股决策。
* **深层护城河引擎 (Deep Moat Engine)**：内置 5 大护城河量化模型，穿透资产负债表与利润表。
* **现代技术栈**：使用 `uv` 进行极致的依赖管理，`FastAPI` 提供异步响应，`Pandas` 进行高性能数据清洗。
* **智能评级系统**：智能评级，对企业进行“宽护城河”与“窄护城河”自动分类。

## 🏗️ 目录架构

```text
app/
├── api/          # 接口层 (基于 FastAPI)
├── core/         # 核心配置 (心学逻辑与参数)
├── db/           # 数据库持久化 (PostgreSQL)
├── models/       # SQLAlchemy 领域模型
├── schemas/      # Pydantic 响应模型
├── services/     # Moat Engine (核心计算逻辑)
└── crud/         # 数据库增删改查

## 启动

```bash
python -m venv .venv
.venv\Scripts\activate.bat
uv sync
```

```bash
uvicorn app.main --host 0.0.0.0 --port 8000 --reload
```


```bash
python app.worker.sync.py --xxx
uv run python -m app.worker.sync --daily
```

低积分推荐（先按关注股票跑）
uv run python -m app.worker.sync --fina_mainbz --mainbz_ts_codes 600600.SH,000001.SZ --mainbz_types P,D --workers 1
全市场增量（跳过已存在）
uv run python -m app.worker.sync --fina_mainbz --mainbz_types P,D --workers 1
全市场强制重刷（最耗积分，不建议频繁）
uv run python -m app.worker.sync --fina_mainbz --mainbz_types P,D --workers 1 --fina_mainbz_force

## scripts 说明

`scripts/` 目录里现在同时存在临时核查脚本、数据筛选脚本、报告生成脚本和浏览器控制台脚本。为了避免“文件名看不出用途”，约定如下：

- 新脚本优先使用中文或中文主语义命名，例如：`查询主营业务近五年.py`、`筛选低估值A股.py`
- 每个脚本文件开头必须补一段中文说明，至少写清楚“作用”和“适用场景”
- 能复用的脚本尽量参数化；一次性实验脚本也至少要说明它是给哪只股票、哪个专项问题服务的

当前脚本用途示例：

- `scripts/查询主营业务近五年.py`：按产品关键字查询 `fina_mainbz` 近五年数据，输出收入、利润、成本、毛利率、同比和 CAGR
- `scripts/screen_low_valuation_a_share.py`：筛选低估值 A 股候选池
- `scripts/filter_high_growth_from_shortlist.py`：从候选池里再筛高增长股票
- `scripts/quality_check_report.py`：单票财务质量检查
- `scripts/analyze_stock_report.py`：生成单票结构化分析报告
- `scripts/analysis_dialogue_report.py`：生成对话式长篇公司分析报告
- `scripts/peer_snapshot.py`：生成简版同业快照
- `scripts/check_sungrow_q4.py`：专项核对阳光电源四季度数据
- `scripts/fetch_api_000513.py`：调试本地股票详情接口
- `scripts/富途牛牛脚本.js`：在富途网页抓取财务表 JSON
- `scripts/东方财富脚本.js`：在东方财富网页导出 CSV

示例：

```bash
uv run python scripts/查询主营业务近五年.py --keyword 储能系统
uv run python scripts/查询主营业务近五年.py --keyword 光伏逆变器
uv run python scripts/quality_check_report.py 600036.SH
uv run python scripts/peer_snapshot.py 招商银行
```

