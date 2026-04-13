# 数据来源与调用说明

本文件只覆盖仓库内本地数据层。Tushare 通用接口请交给外部 `tushare-data` skill。

## 项目内核心文件

- 表定义：`app/models/models.py`
- Tushare 服务：`app/service/tushare_service.py`
- 财务整合：`app/service/finance_service.py`
- 财务指标：`app/service/finance_metrics.py`
- 趋势接口：`app/api/v1/analysis.py`
- 原始数据接口：`app/api/v1/raw_data.py`

## 本地接口抓取脚本

```bash
python scripts/fetch_local_stock_api.py --ts-code 000592.SZ
```

自定义 URL：

```bash
python scripts/fetch_local_stock_api.py --url http://localhost:5100/stock/000592.SZ
```

只检查 URL 与输出路径，不发请求：

```bash
python scripts/fetch_local_stock_api.py --ts-code 000592.SZ --dry-run
```

## 结果约定

- 成功时把 JSON 或文本保存到 `outputs/`。
- 若返回 JSON 且包含 `code` 字段，只有 `code == 200` 视为成功。
- 若用户要求特定股票接口，要在答复里明确告知保存路径。
