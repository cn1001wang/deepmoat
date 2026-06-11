# 组合调用约定

这是硬规则。

## 基础顺序（默认）

1. 外部 `tushare-data`
2. 仅在以下场景再启用本地 `deepmoat-local-data`：
   - 横向比较标的非常多（例如 20+）
   - 用户明确要求“速度优先/尽快返回”

默认完成第 1 步后即可路由到报告类 skill；若启用第 2 步，必要时再回补 `tushare-data` 做关键日期校验。

## 报告路由（不要默认三开）

- 用户要结构化报告：调用 `12-report`
- 用户要对话式分析：调用 `analysis`
- 用户要深度模板化评分：调用 `value-report`
- 用户同时要“结构化 + 对话”：先 `12-report`，再 `analysis`

默认不要同时并行唤醒 `analysis + 12-report + value-report`，避免重复计算与重复文本。

## 外部 `tushare-data` 的目标

- 最新行情与估值日期
- 最新财务与行业背景
- 2-4 条高价值公开来源（公告/官网/权威统计）

## `deepmoat-local-data` 的目标

- 读取 `app/models/models.py` 对应表结构
- 对齐本地口径（重点 `income`、`balancesheet`、`cashflow`、`daily_basic`）
- 明确本地结论和外部结论的边界

## 产物命名建议

统一放在 `outputs/reports/{symbol}_{name}/`，建议：

- `12-report`：`outputs/reports/{symbol}_{name}/r12_{symbol}_{name}_{YYMMDDHHmm}.md`
- `analysis`：`outputs/reports/{symbol}_{name}/analysis_{symbol}_{name}_{YYMMDDHHmm}.md`
- `value-report`：`outputs/reports/{symbol}_{name}/value_{symbol}_{name}_{YYMMDDHHmm}.md`

## 数据冲突处理

- 公共披露新于本地缓存：优先公共披露
- 本地库更新更晚且可验证：优先本地库
- 口径冲突必须显式说明，禁止静默混用
