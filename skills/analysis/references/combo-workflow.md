# 组合调用约定

这是硬规则。

公司分析任务默认按下面顺序执行：

1. 外部 `tushare-data`
2. 本地 `deepmoat-local-data`
3. `analysis`

不能跳过顺序，也不要交换顺序，除非用户明确只要其中一部分。

## 第一步：外部 `tushare-data`

先用外部 `tushare-data` 解决公共数据问题：

- 最新行情与估值
- Tushare 财务数据
- 行业、板块、宏观数据
- 公告、新闻、政策线索

目标：

- 给出最新公共口径
- 明确最新日期
- 找到会影响判断的行业和政策背景
- 在 `deepmoat` 仓库内，默认把外部资料压到最小集：最新价格 + 2-4 条权威公开资料，不重复抓一整套财务明细

如果外部 `tushare-data` 不可用：

- 要明确说明缺口
- 然后退回公开网页或项目已有数据
- 但在结论里注明“未完成外部 skill 校验”

## 第二步：`deepmoat-local-data`

再用本地 skill 对齐项目自己的数据层：

- 读取 `app/models/models.py` 对应的表
- 复用 `app/service/finance_service.py`、`app/service/finance_metrics.py`、`app/service/trend_service.py`
- 记住真实表名是 `balancesheet`、`cashflow`，不是 `balance_sheet`、`cash_flow`
- 检查本地接口
- 把需要保存的接口结果落到 `outputs/`
- 若目标只是生成单票报告，优先复用 `scripts/analysis_dialogue_report.py`

目标：

- 验证仓库本地口径是否支持或修正外部数据
- 补充本地专有字段、横表、用户标签或本地接口内容
- 明确哪些结论来自本地库，哪些来自外部公共数据

## 第三步：`analysis`

只有在前两步完成后，才开始输出对话式分析。

输出时默认做三件事：

- 先让沃伦解释生意、护城河和增长。
- 再让查理拆风险、反驳乐观假设。
- 最后让本杰明插话校准估值和价格。

## 数据冲突时的处理

- 最新且可验证的公共披露，优先于旧的本地缓存。
- 本地库若明显更新到更晚日期，可优先于网页摘要。
- 若两边口径不同，要在报告里直接说清楚，不要悄悄混合。
- 明确区分“价格日期”和“财报日期”；这两个日期不同是常态，不是错误。
- 估值前先核对字段单位，避免 `total_mv`、`total_share`、`netdebt` 被重复换算。

## 最小交付要求

一份完整分析，至少要明确：

- 外部 `tushare-data` 给了什么
- `deepmoat-local-data` 给了什么
- 最终估值基于哪一组日期和股本口径
- 若使用了仓库脚本生成报告，要说明脚本路径与输出文件路径
