---
name: value-report
description: 基于巴菲特+芒格框架生成A股深度价值研究报告。用于用户要求护城河分析、资本配置分析、估值与风险评分、终极三问、幸存者偏差等场景。输出中文并按统一命名规范落盘到 outputs。
---

# value-report

## 职责边界

- 产出深度价值研究报告（重分析、重证据、含评分卡）。
- 必须回答“终极三问”。
- 与 `12-report` 的差异：本 skill 更深、更重，默认包含评分与幸存者偏差检验。
- 最终报告必须是中文。

## 前置顺序（硬规则）

`tushare-data -> deepmoat-local-data -> value-report`

- 必须先查看数据库定义：`app/models/models.py`。
- 核心数据优先本地库：`income`、`balancesheet`、`cashflow`、`fina_indicator`、`daily_basic`、`dividend`、`fina_audit`、`stock_company`。
- 至少覆盖近 3-5 年年度数据；季度数据用于补趋势拐点。
- 涉及“最新/当前/今日”必须写绝对日期。

## 固定图表流程（新增硬规则）

> 不再手工拼图表，不再只保留 ECharts JSON。  
> 必须先用固定脚本批量出图，再把图片回插到报告。

固定脚本：`scripts/render_value_report_charts.py`

### 1) 从草稿生成图表图片

```bash
uv run python scripts/render_value_report_charts.py <草稿md路径>
```

- 默认输出目录：`outputs/charts/<草稿文件名去掉_draft>/`
- 默认输出：
  - `chart_01.svg ...`
  - `charts_snippet.md`（可直接粘贴/回插的 Markdown 图片片段）

### 2) 自动回插到正式报告（推荐）

```bash
uv run python scripts/render_value_report_charts.py <草稿md路径> --inject-report <正式报告md路径>
```

- 会在正式报告写入标记区块：
  - `<!-- VALUE_CHARTS_START -->`
  - `<!-- VALUE_CHARTS_END -->`
- 若区块已存在则覆盖更新，实现重复执行幂等。

### 3) 报告验收规则（必须满足）

- 正式报告中必须出现图表图片区块（`VALUE_CHARTS_START/END`）。
- 图片链接必须可打开（建议绝对路径）。
- 图表与正文结论一致，不能出现“图文口径冲突”。

## 执行流程（标准）

1. 标的识别  
- 优先用用户给的 `ts_code`；若只有名称，先映射 `stock_basic -> ts_code`。

2. 草稿生成（推荐）  
- 运行：
  ```bash
  uv run python scripts/value_report_scaffold.py <股票代码或名称>
  ```
- 草稿命名：`outputs/value_{symbol}_{name}_{YYMMDDHHmm}_draft.md`

3. 图表生成（强制）  
- 运行固定脚本生成图表：
  ```bash
  uv run python scripts/render_value_report_charts.py <草稿md路径>
  ```

4. 外部增量验证  
- 补充公司公告、交易所披露、公司官网、权威行业数据。  
- 外部资料只做“增量验证”，不替代本地财务主口径。

5. 正式报告写作  
- 每节末尾必须有“结论”。
- 结论必须区分“事实”与“推断”。
- 输出多头逻辑、空头逻辑、跟踪指标。
- 输出 100 分评分与分项权重。
- 回答终极三问。

6. 图表回插（强制）  
- 把图表片段插回正式报告（优先自动注入）：
  ```bash
  uv run python scripts/render_value_report_charts.py <草稿md路径> --inject-report <正式报告md路径>
  ```

## 固定章节

1. 公司概况（商业模式优先）  
2. 行业与竞争格局  
3. 护城河分析（含真伪辨别）  
4. 管理层与资本配置  
5. 财务分析（成长/盈利/健康/现金流）  
6. 成长驱动  
7. 风险分析（含幸存者偏差）  
8. 估值分析  
9. 投资判断（多头/空头/跟踪指标）  
10. 最终结论  
11. 总评分（100分）  
12. 三个终极问题（必须回答）

## 输出命名（统一）

- 输出目录：`outputs/`
- 草稿文件：`value_{symbol}_{name}_{YYMMDDHHmm}_draft.md`
- 正式报告：`value_{symbol}_{name}_{YYMMDDHHmm}.md`
- 代码仅保留 6 位数字，不带 `.SH/.SZ`
- 示例：`value_000513_丽珠集团_2604152130.md`

## 快速调用模板（给 AI）

```bash
# 1) 生成草稿
uv run python scripts/value_report_scaffold.py 300232.SZ

# 2) 生成图表
uv run python scripts/render_value_report_charts.py outputs/value_300232_洲明科技_2604151509_draft.md

# 3) 写正式报告（AI写入 outputs/value_300232_洲明科技_2604151509.md）

# 4) 回插图表
uv run python scripts/render_value_report_charts.py \
  outputs/value_300232_洲明科技_2604151509_draft.md \
  --inject-report outputs/value_300232_洲明科技_2604151509.md
```

## 失败兜底

- 本地库缺关键表：先输出可得结论，再列缺失项与影响范围。
- 外部资料检索失败：保留本地定量结论，并明确“外部验证不足”。
- 同指标多口径冲突：默认“本地库主口径 + 公告解释”，并说明差异原因。
- 图表脚本失败：先保留文字版结论，明确“图表生成失败”，并附失败命令与错误摘要。
