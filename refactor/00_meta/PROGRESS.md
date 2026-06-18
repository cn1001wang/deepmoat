# DeepMoat 升级进度

> 自驱 agent 每轮必读必更新。状态值:`pending` / `in_progress` / `done` / `blocked`。

最后更新:2026-06-18(主控提示词从 P1-P9 重构方案改为 P0-P5 升级方案)
当前阶段:**P0 现状盘点**
当前任务:**T0.1**

## 阶段进度

| 阶段 | 状态 | 摘要 |
|------|------|------|
| P0 现状盘点 | in_progress | 6 个清单文件,投资体系 v2 指针 |
| P1 Skills 合并 + 投资体系工具化 | pending | 3 新 skill + 5 个 service + 换仓决策器 |
| P2 云部署 + 自动化抓取 + UI 重构 | pending | 容器化 + 定时任务 + UI v2 |
| P3 AI 报告生成 v1 | pending | 周/月/季报 + 推送 |
| P4 Rust 切片(护城河引擎) | pending | 转岗故事核心,10-14 周 |
| P5 AI Agent v2 | pending(按需) | 浏览器/MCP,看 P3 表现再决策 |

## 任务进度

### P0 现状盘点
- [ ] T0.1 inventory_app.md — pending
- [ ] T0.2 inventory_fe.md — pending
- [ ] T0.3 data_model.md(ER 图) — pending
- [ ] T0.4 routes.md — pending
- [ ] T0.5 frontend_routes.md — pending
- [ ] T0.6 skills_inventory.md — pending
- [x] T0.7 投资体系 v2 指针(已建,投资体系 v2 已草拟) — done

### P1 Skills 合并 + 投资体系工具化
- [ ] T1.1 3 个新 skill 边界设计 — pending
- [ ] T1.2 skill 代码落地 — pending
- [ ] T1.3 skills_design.md — pending
- [ ] T1.4 5 个新 service(growth/moat/value_trap/switch/portfolio) — pending
- [ ] T1.5 对应 v1 路由 + 更新 routes.md — pending
- [ ] T1.6 换仓决策器前端页 — pending
- [ ] T1.7 黄金数据集 5 只票测试 — pending
- [ ] T1.8 investment_prompts.md(卖出/复盘 prompts) — pending
- [ ] T1.9 prompt 接入巴芒 skill — pending

### P2 云部署 + 自动化抓取 + UI 重构
- [ ] T2.1 云服务器选型 ADR — blocked(等用户拍板)
- [ ] T2.2 app 容器化 — pending
- [ ] T2.3 fe 容器化 — pending
- [ ] T2.4 部署脚本 + HTTPS — pending
- [ ] T2.5 简单鉴权 — pending
- [ ] T2.6 抓取定时化 — pending
- [ ] T2.7 抓取失败告警 — pending
- [ ] T2.8 fe PoC 复制 — pending
- [ ] T2.9 tokens.css — pending
- [ ] T2.10 UI 库选型 ADR — blocked(等用户拍板)
- [ ] T2.11 信息架构重组 — pending
- [ ] T2.12 深色模式 — pending
- [ ] T2.13 ECharts 接入 — pending
- [ ] T2.14 移动端适配 — pending

### P3 AI 报告生成 v1
- [ ] T3.1 报告模板设计 — pending
- [ ] T3.2 report_service.py — pending
- [ ] T3.3 推送通道 — blocked(等用户拍板)
- [ ] T3.4 报告归档 — pending

### P4 Rust 切片
- [ ] T4.1 cargo workspace — pending
- [ ] T4.2 axum 服务 + utoipa — pending
- [ ] T4.3 sqlx 连 PG — pending
- [ ] T4.4 护城河算法 PoC — pending
- [ ] T4.5 /v1/moat/score 端点 — pending
- [ ] T4.6 Python HTTP 集成 + fallback — pending
- [ ] T4.7 perf_report.md — pending
- [ ] T4.8 docker-compose 集成 — pending
- [ ] T4.9 tracing + grafana(可选) — pending

### P5 按需

## 待人工决策(影响后续启动)

写在 OPEN_QUESTIONS.md。当前未阻塞 P0 启动,P0 跑完之前用户可以慢慢答:
- Q-0001 3 个新 skill 名字 / 边界
- Q-0002 云服务器选型
- Q-0003 UI 库选型
- Q-0004 推送通道选型

## 本轮备注

**2026-06-18(脚手架建立)**
- 主控提示词 P1-P9 → P0-P5 重写,贴合用户实际目标(个人长期投资工具升级 + Rust 转岗故事)
- 投资体系 v2 完成草稿(14 章 + 2 附录),落 `C:\codes\github\deepvalue\投资体系\投资体系_v2.md`
- 新增 3 条 ADR(005-007)
- 下一步:用户启动长跑,让 agent 跑 P0
