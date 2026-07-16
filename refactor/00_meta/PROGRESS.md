# DeepMoat 升级进度

> 自驱 agent 每轮必读必更新。状态值:`pending` / `in_progress` / `done` / `blocked`。
>
> **权威执行计划**：`05_impl_plan/01_reconciled_plan.md`（Track A-G）。本文件只跟踪状态，不再维护独立的 P0-P5 任务编号。

最后更新:2026-07-16（对账真实代码状态，重写本文件）
当前阶段:**提交基线 -> Track A 地基收尾**
当前任务:**A-1 清理遗留**

## 真实进度对账（2026-07-16）

详见 `05_impl_plan/01_reconciled_plan.md` 第 1 节。要点：
- 工程轨 P0③ 配置加固 / P1① 在线解耦 Tushare / P3 docker+systemd 部署 已完成
- P0①②④⑤ / P1②③ / P2 / P4 / P5 未做
- 产品轨：skills 合并 done（1 个 deepmoat-research），其余未做

## Track 进度

| Track | 状态 | 摘要 |
|------|------|------|
| 基线提交 | in_progress | 13 个未提交 app/fe 文件 + Docker/deploy/tests |
| A 地基收尾 | pending | A-1~A-5 见 reconciled_plan 第 4 节 |
| B 护城河抽核 | pending | moat_engine 权威实现 + golden data |
| C 投资体系工具化 | pending | 5 service + 换仓决策器（依赖 B） |
| D async+仓储+缓存 | pending | 公网压测前做 |
| E 公网加固 | pending | 鉴权/限流/真云/推送（Q-0002/Q-0004 待答） |
| F UI 重构 | pending | 深色/tokens/IA/移动 |
| G Rust 切片 | pending | 转岗故事（依赖 B） |

### Track A 子任务
- [ ] A-1 清理遗留（vercel/.vercel/stock.db/stock_shcemes 重命名/tsbuildinfo 忽略） - in_progress
- [ ] A-2 config 启动校验 - pending
- [ ] A-3 全局异常处理器 + 统一 ResponseOk - pending
- [ ] A-4 事务边界（bulk_upsert 接收外部连接） - pending
- [ ] A-5 Alembic baseline + 退役 init_db - pending

## 待人工决策

写在 OPEN_QUESTIONS.md。Q-0001（skills）/Q-0003（UI 库）已关闭（现实已答）。
- Q-0002 云服务器选型 -> 影响 Track E
- Q-0004 推送通道 -> 影响 Track E

## 本轮备注

**2026-07-16（对账 + 重启）**
- 盘点真实代码：发现 PROGRESS 旧版严重过期（声称 P0 未开始，实际 P0③/P1①/P3 部署已做）
- 发现两套 P0-P5 编号冲突 -> ADR-0008 确认以工程文档为骨架，改用 Track A-G
- 发现 `app/fe` 只读约束已被打破 -> ADR-0008 改为"每步保持可运行 + 增量可回滚"
- 新增 `05_impl_plan/01_reconciled_plan.md` 作为单一事实源
- 关闭 Q-0001/Q-0003
- 下一步：提交基线，进入 Track A

**2026-06-18（脚手架建立）**
- 主控提示词 P1-P9 -> P0-P5 重写
- 投资体系 v2 完成草稿
- 新增 3 条 ADR（005-007）
