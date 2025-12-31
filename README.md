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
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```


```bash
python app.worker.sync.py --xxx
```



