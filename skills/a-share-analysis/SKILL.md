---
name: a-share-analysis
description: 使用 DeepMoat 的财务数据层与巴菲特/芒格/本杰明框架，输出中文 A 股基本面分析与估值报告。
---

# a-share-analysis

当用户要做公司研究、护城河判断、风险审计、估值测算或投研写作时使用本 skill。
默认输出采用“沃伦与查理对话，本杰明穿插补充”的中文对话体。

## 先读什么

1. 阅读 `README.md` 获取项目背景。
2. 从 `app/models/models.py` 确认表结构；不要跳过这一步。
3. 阅读 [references/combo-workflow.md](references/combo-workflow.md)。
4. 公司分析默认必须先调用外部 `tushare-data`。
5. 然后必须调用 `skills/deepmoat-local-data/SKILL.md`。
6. 最后才进入本 skill 的对话式输出。

## 数据原则

- 核心数据至少合并 `income`、`balance_sheet`、`cash_flow`、`daily_basic`。
- 需要质量指标时补充 `fina_indicator`、`fina_audit`、`dividend`。
- 输出分析时要明确数据来源、统计口径和缺口。
- 最终报告始终使用中文输出。
- 角色化表达只改变写法，不改变证据标准；所有判断仍要落在财务和业务事实上。
- 数据调用顺序是硬规则，不是建议：`外部 tushare-data -> deepmoat-local-data -> a-share-analysis`。

## 工作流

1. 先用外部 `tushare-data` 拿最新公共数据：行情、财务、行业、宏观、公告、新闻。
2. 再用 `deepmoat-local-data` 对齐本地数据库、本地接口和 `outputs/` 结果。
3. 将两类数据合并后，再用沃伦口吻解释公司如何赚钱。
4. 让查理直接打断、反驳、拆风险，语气要锋利但不油滑。
5. 在关键处插入本杰明，专门负责估值、假设和数字纪律。
6. 结尾回到三人简短收束，给出“好公司”和“好价格”是否同时成立。
7. 对话里要区分事实、计算结果和推断，不要把角色腔调写成虚构表演。

## 输出骨架

固定使用这四段，但每段内部采用角色对话：

- `【沃伦与查理】`
- `【本杰明插话：估值】`
- `【综合结论】`

更完整的要求见 [references/report-spec.md](references/report-spec.md)。
组合调用顺序见 [references/combo-workflow.md](references/combo-workflow.md)。
角色口吻规则见 [references/dialogue-style.md](references/dialogue-style.md)。
知识库引用规则见 [references/knowledge-base.md](references/knowledge-base.md)。
