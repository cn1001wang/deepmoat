# 统一输出命名规范

> 本文件是所有 skill 输出文件命名的单一来源（Single Source of Truth）。

## 根目录

`outputs/reports/`

## 个股报告

### 目录

`outputs/reports/{symbol}_{name}/`

- `symbol`：6 位股票代码，不带 `.SH/.SZ`
- `name`：公司简称（中文）

### 文件名格式

`{prefix}_{symbol}_{name}_{YYMMDDHHmm}[_{artifact}].md`

### prefix 与 artifact 对照表

| 技能 | prefix | artifact | 示例 |
|------|--------|----------|------|
| analysis | `analysis` | 无 | `analysis_000513_丽珠集团_2604152130.md` |
| 12-report | `r12` | 无 | `r12_000513_丽珠集团_2604152130.md` |
| value-report | `value` | `draft` 或无 | `value_000513_丽珠集团_2604152130_draft.md` |
| AI 估值 | `ai_valuation` | 无 | `ai_valuation_000513_丽珠集团_2606111430.md` |
| 索引文件 | `index` | 无 | `index_000513_丽珠集团_2604152130.md` |

## 筛选报告

### 目录

`outputs/reports/screener/`

### 文件名格式

`screener_{strategy}_{YYMMDDHHmm}.md`

### 示例

- `screener_稳健价值型_2606111430.md`
- `screener_高质量成长型_2606111430.md`
- `screener_高股息低估值型_2606111430.md`
- `screener_困境反转型_2606111430.md`

## 图表目录

value-report 的图表放在：

`outputs/reports/{symbol}_{name}/charts/`

图表文件：`chart_01.svg`, `chart_02.svg`, ...

## 通用约定

- 统一使用下划线 `_` 分隔，不使用连字符 `-`
- 时间戳格式：`YYMMDDHHmm`（2位年+2位月+2位日+2位时+2位分）
- `artifact` 仅在需要区分草稿/中间产物时追加
- 同一只股票的所有产物必须落在同一股票目录中
