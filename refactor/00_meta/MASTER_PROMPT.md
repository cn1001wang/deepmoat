# DeepMoat 升级 · 主控提示词(自驱 Agent 入口)

> 启动方式:把 "## 主控提示词正文" 整段 copy 给一个长跑的 Claude(或 Workflow 的根 agent)。
> 续跑方式:直接 `cat refactor/00_meta/MASTER_PROMPT.md` 再贴给 agent,它会自己读 PROGRESS.md 接着干。

---

## 项目目标(已拍板)

DeepMoat 是用户的**个人长期投资工具**。本次升级目标(按优先级):

1. **投资体系工具化**(第一性)— 把 `C:\codes\github\deepvalue\投资体系\投资体系_v2.md` 中可量化的部分落到代码,形成"换仓决策器、组合健康度、4 种评分模式、AI 复盘对话"等具体功能
2. **Skills 整合** — `.claude/skills/` 下多个 skill 合并为 3 个:统一入口 / 分析 / 巴菲特芒格问答
3. **云端部署 + 自动化抓取** — 部署到云服务器(后续选型),Tushare 抓取改定时任务,支持手机/外出电脑访问
4. **AI 报告生成 v1** — 定时跑 → AI 调用 → 生成 markdown 报告 → 推送
5. **UI 重构(保留 Vue 3)** — UI 库升级 + 设计 token + 深色模式 + ECharts + 信息架构按 v2 体系重组
6. **Rust 切片转岗故事** — 把"护城河引擎"切出来用 Rust(axum + sqlx)独立微服务,Python 主体不变,通过 HTTP 调用。**这是用户后端转岗的核心面试故事**
7. **AI Agent v2** — 浏览器调用 / MCP 等高级能力(看 P3 表现后再决策,可无限期推迟)

## 不变约束(违反即停下,写到 OPEN_QUESTIONS.md)

1. 工作根目录:`C:\codes\github\deepmoat`
2. **只读区**:`app/`、`fe/`、`scripts/`、`README.md`、`AGENTS.md`、`Clippings/`、`obsidian/`、`outputs/`、`outputs_old/`、`tests/`、`pyproject.toml`、`uv.lock`、`vercel.json`、`Users/`、根目录中文 md 笔记
3. **可写区**:`refactor/` 下全部内容(含 `_workspace/` 内 Rust / 前端 PoC)、`.claude/skills/`(如果改 skill 需要落代码,在 P1 阶段开放)
4. **投资体系权威版本**:`C:\codes\github\deepvalue\投资体系\投资体系_v2.md`(deepvalue 仓库)。本仓库的 `refactor/02_specs/investment_system.md` 只是入口指针,不复制内容
5. 任何对 `app/` / `fe/` 的修改诉求 → 先写进 `OPEN_QUESTIONS.md`,等用户答复
6. **不删除 Python 后端**。Rust 切片(P4)是补充,不是替代;Python 是生产工具,Rust 是独立微服务
7. 涉及外部网络(Tushare、AI API)只在测试阶段用 mock;**禁止**把真实 token / API key 写进任何文档或代码
8. 每完成一个任务:① 更新 `PROGRESS.md` ② 在 `DECISIONS.md` 追加决策(如有)③ 提交 git,消息格式 `refactor(P{n}): {摘要}`
9. 单次 Read 不超过 1500 行;先 Glob/Grep 定位再读局部
10. 所有产出文档**中文**;代码注释中英文混用按既有风格
11. 每写 Mermaid 图先脑内过语法

---

## 阶段编号与门禁

| 阶段 | 名称 | 主产物 | DoD 摘要 |
|------|------|-------|---------|
| **P0** | 现状盘点 | inventory_app/fe.md / data_model.md / routes.md / frontend_routes.md / skills_inventory.md | 6 文件齐;ER 图能渲染;路由清单字段齐 |
| **P1** | Skills 合并 + 投资体系工具化 | 3 个新 skill / 投资体系 service 集 / 换仓决策器 | 旧 skills 退役;3 个新 skill 跑通;换仓决策器有 UI 并可用 |
| **P2** | 云部署 + 自动化抓取 + UI 重构 | Dockerfile / docker-compose / Tushare 定时任务 / UI v2(深色模式 + 设计 token + ECharts) | 云服务器跑通 + HTTPS + 移动端访问 + 抓取每日自动 |
| **P3** | AI 报告生成 v1 | 报告模板 / 定时任务 / 推送通道 | 周报自动生成 + 推送到手机 |
| **P4** | Rust 切片(护城河引擎) | _workspace/backend/ Rust 微服务 | axum 服务跑起来 + sqlx 连 PG + 移植 ROIC + 1 个端点 + Python 主体 HTTP 集成 + 性能对比 |
| **P5** | AI Agent v2 | (按需) | 看 P3 后再决策 |

---

## 工作循环(每轮严格执行)

1. 读 `PROGRESS.md` 确认当前阶段与下一项任务编号
2. 检查 `OPEN_QUESTIONS.md`:阻塞当前则跳过去做不阻塞任务;全阻塞则进入待命态汇总输出
3. 执行任务(读源 → 写文档 / 写代码 / 写测试)
4. 过自检清单
5. 更新 `PROGRESS.md`(in_progress / done 都要标)
6. `git add refactor/ ... && git commit -m "refactor(P{n}): {摘要}"`
7. 进入下一轮

## 自检清单(每轮必过)

- [ ] 没有改动只读区
- [ ] 新文档顶部写了:DoD、最后更新时间、依赖的上游文档
- [ ] Mermaid 图能渲染
- [ ] 关键决定已写进 `DECISIONS.md`
- [ ] PROGRESS 反映真实状态
- [ ] 卡住的事进了 OPEN_QUESTIONS,不硬猜
- [ ] 没泄露真实 token / DB 密码

## 卡死兜底

- 同任务连续失败 3 次 → 写 OPEN_QUESTIONS,跳过
- 连续两阶段无新进展 → 暂停,输出"待人工决策"汇总,进入待命态

---

## 阶段任务库

### P0 现状盘点 (3-4 周)

> 目的:把现状文档化,让 P1+ 不在迷雾中决策。**不重构、不写产品代码**。

- **T0.1** `01_discovery/inventory_app.md`:`app/` Python 模块清单
  - 表头:`| 路径 | 类型 | 一句话职责 | 关键符号 | 外部依赖 | 风险/坏味 |`
  - 不复制源码;末尾追加"下阶段需继承的关键事实"
- **T0.2** `01_discovery/inventory_fe.md`:`fe/` 清单(路由 / 视图 / 组件 / API)
- **T0.3** `01_discovery/data_model.md`:从 `app/models/models.py` 抽 SQLAlchemy 表 → ER 图(Mermaid)
- **T0.4** `01_discovery/routes.md`:`app/api/v1/` FastAPI 路由(method / path / 入参 / 出参)
- **T0.5** `01_discovery/frontend_routes.md`:`fe/src/router` × `views` 对应关系
- **T0.6** `01_discovery/skills_inventory.md`:`.claude/skills/` 现有 skill 清单(每个:用途、输入、输出、调用方式、是否还在用)
- **T0.7** `02_specs/investment_system.md` 已存在(指针),与 deepvalue 的 v2 保持一致 — **只读 v2,不改本文件指针映射表以外内容**

### P1 Skills 合并 + 投资体系工具化 (5-7 周)

> 目的:让投资体系真正能被工具调用,而不是只活在 markdown 里。

#### 1A:Skills 合并

- **T1.1** 基于 T0.6,设计 3 个新 skill 的边界
  - `deepmoat-entry`:统一入口,根据用户问题路由到下面两个
  - `deepmoat-analyze`:股票分析(基本面 + 三表 + 估值,直接 ts_code 输入)
  - `deepmoat-buffett-munger`:巴菲特/芒格风格的对话型 skill(不灌输观点,只问问题,辅助用户思考)
- **T1.2** 落 skill 代码(`.claude/skills/`),提交后旧 skill 标 deprecated
- **T1.3** 写 skill 使用说明 → `02_specs/skills_design.md`

#### 1B:投资体系可量化部分服务化

- **T1.4** 在 `app/service/` 下新增 / 改造(注意:这是 P1 唯一可写 app/ 的口子,**仅添加新文件,不改老文件**;改老文件需走 OPEN_QUESTIONS):
  - `growth_score_service.py` — 投资体系第六章成长能力评分
  - `moat_score_service.py` — 投资体系第七章护城河评分(本服务 P4 会被切到 Rust)
  - `value_trap_service.py` — 投资体系第三章捡漏 vs 价值陷阱判定
  - `switch_decision_service.py` — 投资体系第十一章换仓决策器
  - `portfolio_health_service.py` — 投资体系第十二章组合健康度
- **T1.5** 在 `app/api/v1/` 加对应路由(同样**只新增不改老**);更新 `routes.md`
- **T1.6** 在 `fe/` 加换仓决策器页(原则不动老页,新增 `views/switch-decision.vue`),其余服务先用 Swagger UI 验证,不急做前端
- **T1.7** 测试:每个新 service 至少 5 例黄金数据(招行 / 阳光 / 平安 / 茅台 / 宁德),结果落 `06_tests/golden_data/`

#### 1C:投资体系不可量化部分变 prompt

- **T1.8** `02_specs/investment_prompts.md`:整理出
  - 卖出决策对话 prompt(场景 A/B/C 路径)
  - 月度复盘 prompt(13.2 模板)
  - 季度复盘 prompt(13.3 七问)
  - 年度复盘 prompt(13.4 五问)
- **T1.9** 把这些 prompt 接进 `deepmoat-buffett-munger` skill

### P2 云部署 + 自动化抓取 + UI 重构 (4-6 周)

#### 2A:云部署

- **T2.1** 云服务器选型决策(写进 `DECISIONS.md`):**待用户拍板** — 阿里云轻量 / Hetzner / DigitalOcean / 腾讯云;PG 自托管 vs RDS;域名 + HTTPS 方案
- **T2.2** `app/` 容器化:`refactor/_workspace/deploy/Dockerfile.api` + `Dockerfile.worker` + `docker-compose.yml`
- **T2.3** `fe/` 容器化(nginx 静态托管)
- **T2.4** 部署脚本 + reverse proxy(Caddy / nginx)+ 自动 HTTPS(Let's Encrypt)
- **T2.5** 简单鉴权:HTTP Basic 或 token-in-header(单人用,够了);不要做完整账户体系

#### 2B:自动化抓取

- **T2.6** 现有 `app/worker/sync.py` 改成可定时调用形式(已经是 CLI,主要补 systemd timer 或 cron 配置)
- **T2.7** 抓取失败告警(简单的:失败 → AI API 发邮件给用户)

#### 2C:UI 重构(保留 Vue 3)

- **T2.8** 在 `refactor/_workspace/frontend/` 复制 `fe/` 作为 PoC(不动原 fe/);**注意:UI 重构成功后再 merge 回 fe/,merge 时机由用户决定,merge 前 fe/ 仍是只读**
- **T2.9** 抽 `tokens.css`(颜色 / 字号 / 间距 / 圆角)
- **T2.10** UI 库选型:Naive UI vs Element Plus vs Ant Design Vue → 写到 `04_design/frontend_redesign.md`
- **T2.11** 信息架构按投资体系 v2 重组:
  - 一级导航:观察池 / 持仓 / 换仓决策 / 复盘 / 行业看板 / AI 分析
  - 移除冗余页面,合并相似页面
- **T2.12** 深色模式
- **T2.13** ECharts(替换现有图表)
- **T2.14** 移动端适配(主要是组合健康度 + AI 报告 + 换仓决策器三页能在手机上看)

### P3 AI 报告生成 v1 (2-3 周)

- **T3.1** 报告模板设计 → `02_specs/report_templates.md`
  - 周报:观察池更新 + 持仓变化 + 关键事件
  - 月报:13.2 模板自动填充
  - 季报:13.3 七问 → AI 引导用户回答
  - 公司专题报告:单股票深度
- **T3.2** 实现:`app/service/report_service.py`(单文件即可,不复杂)
- **T3.3** 推送通道:微信(server 酱) / 邮件 / Telegram → 用户选
- **T3.4** 报告归档:存到 PG `reports` 表,前端有列表页

### P4 Rust 切片:护城河引擎(转岗故事) (10-14 周)

> 用户后端转岗的核心故事。完整经历 axum + sqlx + tokio + utoipa + 部署 + 监控 + 测试。

- **T4.1** 在 `refactor/_workspace/backend/` 起 cargo workspace
  - crate:`deepmoat-moat-svc`(微服务主体)/ `deepmoat-moat-core`(算法)/ `deepmoat-moat-data`(repo)
- **T4.2** `deepmoat-moat-svc`:axum 路由 + utoipa + Swagger UI + `/health`
- **T4.3** `deepmoat-moat-data`:sqlx 连 PG,跑通最简 query
- **T4.4** `deepmoat-moat-core`:移植 Python `app/service/moat_engine.py` 的核心算法(护城河 5 维评分),作 PoC
- **T4.5** API:`POST /v1/moat/score`,输入 ts_code,输出护城河评分
- **T4.6** Python 主体集成:`app/service/moat_score_service.py` 通过 HTTP 调用 Rust 服务,降级到本地 Python 实现作为 fallback
- **T4.7** 性能对比:Rust vs Python,数据采样,落 `08_rust_slice/perf_report.md`
- **T4.8** 部署:Rust 服务进 docker-compose,与 Python 主体同台部署
- **T4.9** 监控:tracing 日志接 grafana(可选,看时间)

强约束:
- 不污染仓库根;workspace 在 `refactor/_workspace/backend/`
- thiserror(lib) + anyhow(bin) 分层
- IO 用 tokio;阻塞计算 spawn_blocking
- 配置走 figment + env,禁硬编码
- 移植任何 Python 算法 → 同 PR 加 1 条 golden_data 对照
- 每 commit `cargo fmt && cargo clippy -- -D warnings` 必过

### P5 AI Agent v2(按需)

不预先排期。看 P3 简化版报告够不够用,如果用户不满意再启动:
- 浏览器调用(playwright-mcp / browser-use)
- 多步骤 agent loop
- 工具链扩展

---

## 启动指令(agent 第一次执行)

1. 读本文件全文
2. 读 `PROGRESS.md` 确认起点(首次为空 → 从 P0.T0.1 开始)
3. 读 `02_specs/investment_system.md` 找到投资体系 v2 路径,确认 v2 已存在
4. 进入工作循环

## 给用户的 4 个待答问题(影响后续阶段)

1. **P1A skills 设计** — 3 个新 skill 名字 / 边界 / 是不是这么切?
2. **P2A 云服务器** — 选什么?域名有没有?
3. **P2C UI 库** — Naive UI / Element Plus / Ant Design Vue 倾向?
4. **P3 推送通道** — 微信(server 酱) / 邮件 / Telegram?

> 这 4 个不影响 P0 启动,P0 跑完之前可以慢慢答。
