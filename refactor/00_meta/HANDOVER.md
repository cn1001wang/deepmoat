# DeepMoat 升级 · 交接文档

> **新电脑接手第一份要读的文档。** 读完这一份你就有完整上下文。
>
> 本文档记录"对话外的隐性信息":用户画像、决策上下文、TODO,以及与 AI 续聊的提示词模板。
>
> 最后更新:2026-06-18

---

## 1. 仓库与文档地图

```
C:\codes\github\deepmoat\               # 本仓库:DeepMoat 工程主体
├── app\                                # Python 后端(只读)
├── fe\                                 # Vue 前端(只读)
├── .claude\skills\                     # 待整合的 skills(P1 阶段开放修改)
└── refactor\                           # 本次升级所有产物
    ├── 00_meta\
    │   ├── HANDOVER.md                 # ★ 本文件
    │   ├── MASTER_PROMPT.md            # 自驱主控提示词(给 agent 跑)
    │   ├── PROGRESS.md                 # 阶段任务进度
    │   ├── DECISIONS.md                # ADR 决策记录(7 条)
    │   └── OPEN_QUESTIONS.md           # 4 个待你拍板的问题
    ├── 01_discovery\                   # P0 现状盘点产物(待跑)
    ├── 02_specs\
    │   └── investment_system.md        # 投资体系 → DeepMoat 落地映射(指针)
    ├── 03_api\  04_design\  05_impl_plan\  06_tests\
    └── _workspace\                     # P4 Rust + P2 前端 PoC 落点(待建)

C:\codes\github\deepvalue\              # 用户私人投资体系仓库
└── 投资体系\
    ├── 投资体系整理.md                  # v1(历史保留)
    └── 投资体系_v2.md                   # ★ 投资体系权威版本,DeepMoat 的业务规格输入
```

**关键约定**:投资体系 v2 在 deepvalue,**不复制到 deepmoat**。两边通过 `refactor/02_specs/investment_system.md` 这份指针文件做映射。

---

## 2. 用户画像(给新会话的 AI 看,别让它从头猜)

### 2.1 角色

- **职业**:前端架构师(创业公司)
- **背景**:电子信息工程出身,做过 EMS、工业物联网平台、机器人、ROS
- **职业目标**:公司内部转岗后端 / Web,Rust 是为这个目标服务的学习投资
- **未来方向**:机器人创业(自己做,不通过股票投资同行业)

### 2.2 投资画像

- **资金性质**:个人长期闲钱,小资金量,5 年内不需要赎回
- **风险偏好**:较大风险敞口可接受(因资金量小)
- **投资风格**:价值投资 + 捡漏型
- **能力圈 A 档**:储能(系统集成 / EMS 软件 / BMS / PCS)、消费、AI Agent 国内厂商
- **能力圈 A- 档**(学习中):游戏(研发/渠道/IP)
- **能力圈 B 档**(观察不投):工业自动化 / 机器人零部件(关节);重点跟踪宇树、智元、特斯拉
- **能力圈 C 档**(不碰):金融、地产、周期资源、生物科技、半导体设备、航空航运
- **卖出体系**:场景 B 一定卖,场景 C 走多情景胜率换仓决策器,场景 A 一般不卖

### 2.3 时间投入

- 工作日 1-2 小时
- 周末 12 小时(周六周日各 6 小时)
- 总计约 **13 小时/周**

### 2.4 升级 DeepMoat 的 7 个真实诉求(按优先级)

1. **投资体系工具化** — 把投资体系 v2 中可量化的部分变成具体功能(换仓决策器、组合健康度、4 模式评分等)
2. **Skills 整合** — `.claude/skills/` 多个 skill → 3 个(统一入口 / 分析 / 巴菲特芒格问答)
3. **云端部署 + 自动化抓取** — 部署到云,Tushare 抓取定时,移动端可访问
4. **AI 报告生成 v1** — 简化版,不上 agent loop / 浏览器调用
5. **UI 重构** — 保留 Vue 3,UI 库升级 + 设计 token + 深色模式 + ECharts + 信息架构按 v2 体系重组
6. **Rust 切片(护城河引擎)** — 转岗故事核心,Python 主体不变,Rust 独立微服务
7. **AI Agent v2** — 浏览器/MCP,可无限期推迟

---

## 3. 决策上下文(为什么这么定的)

### 3.1 战略转向

- 原方案是 P1-P9 的 Rust 全栈重构(`MASTER_PROMPT.md` 旧版,见 git 历史)
- **改为 P0-P5 渐进升级 + Rust 切片**(详见 `DECISIONS.md` ADR-0005)
- 原因:用户单人用 + 转岗目标 + 时间 13h/周 → 全栈重构投入产出比差,渐进升级 + 一个清晰的 Rust 切片更划算

### 3.2 已锁定的技术选型

| 项 | 取值 | ADR |
|----|-----|-----|
| 后端 Web 框架 | axum | 0001 |
| 数据库 | PostgreSQL | 0002 |
| 前端方向 | 保留 Vue 3,只做 UI 美化 | 0003 |
| 数值库 | polars | 0004 |
| 升级方式 | 渐进升级 + Rust 切片 | 0005 |
| 投资体系存储 | deepvalue 仓库,DeepMoat 只放指针 | 0006 |
| Rust 切片选择 | 护城河引擎(`app/service/moat_engine.py`) | 0007 |

### 3.3 还在等你拍板的(`OPEN_QUESTIONS.md`)

| 编号 | 问题 | agent 倾向 |
|------|------|-----------|
| Q-0001 | 3 个新 skill 命名 | `deepmoat-entry` / `deepmoat-analyze` / `deepmoat-buffett-munger` |
| Q-0002 | 云服务器选型 | Hetzner CX22 €4.5/月 + Cloudflare;或阿里云香港轻量 30/月 |
| Q-0003 | UI 库 | Naive UI |
| Q-0004 | 推送通道 | server 酱(微信)+ 邮件兜底 |

不阻塞 P0 启动。P0 跑完之前慢慢答。

---

## 4. 当前进度

- **当前阶段**:P0 现状盘点(`in_progress`,刚启动还没跑)
- **当前任务**:T0.1 `inventory_app.md`
- **已完成**:
  - 投资体系 v2 草稿落盘(deepvalue 仓库)
  - DeepMoat 重构脚手架建立
  - 主控提示词 P1-P9 → P0-P5 完全重写
  - 7 条 ADR 落地
  - 4 个 Q 已开

详细任务清单见 `PROGRESS.md`。

---

## 5. 切电脑前 TODO(在旧电脑上做完)

### 5.1 deepmoat 仓库

```bash
cd C:\codes\github\deepmoat
git status                              # 确认改动符合预期
git add refactor/
git commit -m "refactor: 主控提示词重构为 P0-P5 渐进升级方案 + 投资体系 v2 映射"
git push
```

### 5.2 deepvalue 仓库 ⚠️ 谨慎

```bash
cd C:\codes\github\deepvalue
git status                              # 重要!里面有几个旧文件被标 deleted

# 旧"投资体系整理.md"等几个文件被标 deleted。
# 在 commit 前确认:
#   1. 这些 deletion 是不是你想要的(可能是其他电脑或之前的整理)
#   2. 如果不确定,先备份:
git stash
# 这样 deletions 暂时藏起来,新电脑你可以再 git stash pop 回看
# 或者:
git restore <被删的文件路径>            # 恢复

# 确认 OK 后:
git pull --rebase                       # 你 origin/main 落后 3 个 commit,先拉
git add 投资体系/投资体系_v2.md
git commit -m "feat: 新增投资体系 v2(14 章 + 2 附录)"
git push
```

### 5.3 验证

打开 GitHub 网页确认两个仓库都显示了最新 commit。

---

## 6. 新电脑上的接手流程

### 6.1 启动一个新 Claude Code 会话

进入 `C:\codes\github\deepmoat`(或你新电脑的对应路径),启动 Claude Code:

```bash
cd /path/to/deepmoat
claude --dangerously-skip-permissions
```

### 6.2 给 AI 的接手提示词(整段 copy 粘贴)

```text
你正在续接 DeepMoat 升级项目。

第一步,读以下文档(按顺序):
1. refactor/00_meta/HANDOVER.md             — 完整上下文
2. refactor/00_meta/MASTER_PROMPT.md        — 自驱主控提示词
3. refactor/00_meta/PROGRESS.md             — 当前任务进度
4. refactor/00_meta/DECISIONS.md            — 已锁定的 7 条 ADR
5. refactor/00_meta/OPEN_QUESTIONS.md       — 4 个待用户拍板的问题
6. refactor/02_specs/investment_system.md   — 投资体系映射(指针)
7. C:\codes\github\deepvalue\投资体系\投资体系_v2.md   — 投资体系权威版本(在另一仓库)

读完后告诉我:
- 当前应该做的下一项任务编号
- 你对当前任务的执行计划(3-5 步)
- 是否有阻塞或需要我先答的问题

不要自动启动长跑,等我说"开始 P0"再进入工作循环。
```

### 6.3 三种续接动作可选

**动作 A:继续填投资体系 v2 待补章节**(对话型)

```
我想继续补投资体系 v2 附录 B 的待补清单。
我们继续上次的对话,你扮演巴菲特+芒格风格的提问者,问我消费板块的具体子赛道。
```

**动作 B:启动 P0 现状盘点**(自驱型)

```
按 MASTER_PROMPT 进入工作循环,从 T0.1 开始。
P0 是纯文档,跑废概率低,放心做。
做完一个任务停下来汇报,等我看完再放下一个。
```

**动作 C:答 4 个 OPEN_QUESTIONS**

```
我现在答 OPEN_QUESTIONS.md 中的 Q-0001:...
我现在答 Q-0002:...
你把答案写进 DECISIONS.md 形成 ADR-0008/0009/...,并把对应任务从 blocked 改成 pending。
```

---

## 7. 给 AI 的硬性约束(每次新会话提醒)

如果新会话的 AI 表现不像我们之前对话的样子,贴这段提醒它:

```text
重要约束:
1. 只读区:app/、fe/、scripts/、根目录 *.md(除非用户明确允许)
2. 可写区:refactor/ 全部、.claude/skills/(P1 阶段开放)
3. 投资体系权威版本在 C:\codes\github\deepvalue\投资体系\投资体系_v2.md,**不复制到 deepmoat**
4. 不写真实 token / 密码到任何文件
5. 改任何 app/ 或 fe/ 必须先写 OPEN_QUESTIONS,不许直接动手
6. 单次 Read 不超 1500 行
7. 决策必须落 DECISIONS.md(ADR 格式)
8. 卡住的事写 OPEN_QUESTIONS.md,不要硬猜
9. 文档用中文,代码注释中英文混用按既有风格
```

---

## 8. 完整 TODO(新电脑接手后立刻可做的)

按推荐优先级:

### 立刻做(不依赖任何决策)

- [ ] **T0.1 inventory_app.md** — 跑 P0 第一项,纯读代码 + 写文档
- [ ] **T0.2 inventory_fe.md** — 同上
- [ ] **T0.3 data_model.md** — 抽 SQLAlchemy 表 + ER 图
- [ ] **T0.4 routes.md** — 抽 FastAPI 路由
- [ ] **T0.5 frontend_routes.md** — 抽 Vue 路由
- [ ] **T0.6 skills_inventory.md** — 抽 .claude/skills/ 现状

### 抽空和 AI 对话补完(依赖你的输入)

- [ ] 投资体系 v2 附录 B 待补清单:
  - [ ] 2.2 消费板块的具体子赛道(你日常关注的品牌)
  - [ ] 3.1 实际资金量级 + 期望年化目标
  - [ ] 6 章 你历史上买过的成长股案例
  - [ ] 7 章 你历史上买过的护城河型案例
  - [ ] 12.2 你目前真实组合 vs 默认配置
  - [ ] 13 章 复盘旧记录是否要导入

### 决策类(影响后续阶段启动)

- [ ] 答 Q-0001(skill 命名)→ 影响 T1.1/T1.2
- [ ] 答 Q-0002(云服务器)→ 影响 T2.1-T2.5
- [ ] 答 Q-0003(UI 库)→ 影响 T2.10/T2.11
- [ ] 答 Q-0004(推送通道)→ 影响 T3.3

### 动手类(P0 完成后才做)

- [ ] P1 启动:Skills 合并 + 投资体系工具化
- [ ] P2 启动:云部署 + 自动化抓取 + UI 重构
- [ ] P3 启动:AI 报告生成 v1
- [ ] P4 启动:Rust 切片(护城河引擎,转岗故事核心)
- [ ] P5 决策:AI Agent v2 是否启动

---

## 9. 联系上下文(保险起见)

- 用户名(git):gdkk
- 用户职位:前端架构师 / 学 Rust 转后端
- 项目动机:个人长期投资工具 + 转岗练手
- 项目风格:工程化 + 心学(知行合一)+ 价值投资
- 时区:中国
- AI 续聊默认语言:中文

---

## 附:旧主控提示词去哪了?

之前的 P1-P9 全栈重构主控提示词被 ADR-0005 替代,但保留在 git 历史里。需要回看的话:

```bash
git log --all -- refactor/00_meta/MASTER_PROMPT.md
git show <旧 commit>:refactor/00_meta/MASTER_PROMPT.md
```

替代它的就是当前版本(P0-P5)。
