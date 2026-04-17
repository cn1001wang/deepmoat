---
name: deepmoat-local-data
description: 读取 DeepMoat 的本地数据库和本地 HTTP 接口，并在需要时把接口结果保存到 outputs；设计为外部 tushare-data skill 的补充。
---

# deepmoat-local-data

当用户要查项目本地数据库、本地 HTTP 接口、仓库内财务整合逻辑，或明确要求把结果保存到 `outputs/` 时使用本 skill。
这个 skill 不负责替代外部 `tushare-data`。

## 触发条件（硬规则）

- 不作为默认数据链路，默认优先外部 `tushare-data`。
- 仅在以下场景优先触发本 skill：
  - 横向比较标的非常多（例如 20+，或用户要大范围批量筛选/排序）。
  - 用户明确提出“速度优先/尽快返回”，可接受基于本地缓存的数据。
  - 用户明确要求读取本地数据库或本地 HTTP 接口。
- 本地缓存来源于 `tushare-data`；若任务要求“最新/当前/今日”口径，关键结论需再用 `tushare-data` 回补日期或抽样校验。

## 数据源顺序

1. 先看 `app/models/models.py`，确认字段与表名。
2. 优先复用仓库已有服务：
   - `app/service/tushare_service.py`
   - `app/service/finance_service.py`
   - `app/service/finance_metrics.py`
   - `app/service/trend_service.py`
3. 若用户需要 Tushare、宏观、行业、公告等通用外部数据，优先切换到外部 `tushare-data` skill。
4. 用户提供本地 HTTP 接口时，优先读取本地接口并保存结果。

## 本地接口规则

- 默认兼容 `http://localhost:5100/stock/{ts_code}`。
- 默认响应格式：

```json
{
  "code": 200,
  "data": {},
  "message": "success"
}
```

- 对 `stock/000592.SZ` 这类接口，结果默认保存到 `outputs/stock-000592-SZ.json`。
- 通用抓取脚本：`.agents/skills/deepmoat-local-data/fetch_local_stock_api.py`

## 与外部 tushare-data 的边界

- 外部 `tushare-data` 负责通用 Tushare 取数。
- 本 skill 负责项目已有的本地数据层和本地接口。
- 若两者都要用，先用外部 `tushare-data` 拿最新公共数据，再用本 skill 对齐本地库和接口口径。

## 常用任务

- 读取四表并做基本面分析。
- 用 `daily_basic` + 三大报表计算估值、盈利、偿债与现金流指标。
- 拉取本地接口结果并落盘到 `outputs/`。
- 当用户给出筛选条件时，先过滤再分析。

更细的来源和脚本用法见 [references/data-sources.md](references/data-sources.md)。
