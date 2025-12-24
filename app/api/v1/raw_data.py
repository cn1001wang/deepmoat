import os
import sys
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------------
# 路径兼容处理
# ------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

# 导入原有业务逻辑
from app.crud.stock import get_stock_basic_all
from app.crud.crud_company import get_stock_company
from app.crud.crud_industry import get_sw_industry, get_index_member
from service.tushare_service import (
    get_balancesheet_all,
    get_cashflow_all,
    get_income_all,
)
from utils.date_utils import generate_periods
from utils.df_utils import dedup_finance_df

# ------------------------
# FastAPI 应用配置
# ------------------------
app = FastAPI(
    title="DeepMoat Finance API",
    description="基于 FastAPI 的基本面分析系统",
    version="1.0.0"
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# 配置常量
# ------------------------
INCOME_COLUMNS = ["revenue", "n_income", "n_income_attr_p", "operate_profit", "basic_eps", 
                  "oper_cost", "sell_exp", "admin_exp", "rd_exp", "fin_exp", "total_profit"]
BALANCE_COLUMNS = ["total_assets", "total_liab", "total_hldr_eqy_exc_min_int"]
CASHFLOW_COLUMNS = ["n_cashflow_act", "n_cashflow_inv_act", "n_cash_flows_fnc_act", "n_incr_cash_cash_equ"]

# ------------------------
# 工具函数 (内部逻辑保持不变)
# ------------------------

def _ensure_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["end_date"] + cols)
    df = dedup_finance_df(df)
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[["end_date"] + cols]

def _filter_periods(df: pd.DataFrame, years: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    start_year = datetime.today().year - years + 1
    periods = set(generate_periods(start_year))
    latest = df["end_date"].max() if "end_date" in df.columns else None
    filtered = df[df["end_date"].isin(periods)]
    if latest:
        filtered = pd.concat([filtered, df[df["end_date"] == latest]], ignore_index=True)
    filtered = filtered.drop_duplicates(subset=["end_date"])
    return filtered.sort_values("end_date", ascending=False)

def _merge_frames(frames: List[pd.DataFrame]) -> pd.DataFrame:
    valid = [f for f in frames if f is not None and not f.empty]
    if not valid: return pd.DataFrame()
    merged = valid[0]
    for f in valid[1:]:
        merged = pd.merge(merged, f, on="end_date", how="outer")
    return merged.sort_values("end_date", ascending=False)

def _safe_div(a, b):
    if pd.isna(a) or pd.isna(b) or b in (0, 0.0): return pd.NA
    try: return float(a) / float(b)
    except: return pd.NA

def _yoy(current_map: Dict[str, float], md: str) -> Dict[str, float]:
    out = {}
    for end_date, cur_val in current_map.items():
        if not end_date or len(end_date) != 8:
            out[end_date] = pd.NA
            continue
        y, mmdd = int(end_date[:4]), end_date[4:]
        prev_key = f"{y-1}{md or mmdd}"
        prev_val = current_map.get(prev_key)
        out[end_date] = (cur_val - prev_val) / prev_val if prev_val not in (None, 0) and not pd.isna(prev_val) else pd.NA
    return out

def _to_billion(val):
    return float(val) / 1e8 if not pd.isna(val) else None

def _format_percent(val):
    return float(val) * 100.0 if val is not None and not pd.isna(val) else None

# ------------------------
# 核心业务逻辑
# ------------------------

def build_metrics_table(ts_code: str, years: int = 6) -> Dict[str, Any]:
    income = _ensure_columns(get_income_all(ts_code), INCOME_COLUMNS)
    balance = _ensure_columns(get_balancesheet_all(ts_code), BALANCE_COLUMNS)
    cash = _ensure_columns(get_cashflow_all(ts_code), CASHFLOW_COLUMNS)

    income = _filter_periods(income, years)
    balance = _filter_periods(balance, years)
    cash = _filter_periods(cash, years)

    merged = _merge_frames([income, balance, cash])
    if merged.empty:
        return {"periods": [], "rows": []}

    periods = list(merged["end_date"])
    revenue_map = dict(zip(merged["end_date"], merged["revenue"]))
    assets_map = dict(zip(merged["end_date"], merged["total_assets"]))

    revenue_yoy_map = _yoy(revenue_map, "1231")
    assets_yoy_map = _yoy(assets_map, "1231")

    def row_values(fn):
        return [fn(r) for _, r in merged.iterrows()]

    rows = [
        {
            "label": "资产合计", "key": "total_assets", "unit": "亿", "category": "资产扩张能力",
            "values": row_values(lambda r: _to_billion(r.get("total_assets"))),
        },
        {
            "label": "资产合计同比增长", "key": "assets_yoy", "unit": "%", "category": "资产扩张能力",
            "values": [_format_percent(assets_yoy_map.get(p)) for p in periods],
        },
        {
            "label": "资产负债率", "key": "debt_ratio", "unit": "%", "category": "业务风险",
            "values": row_values(lambda r: _format_percent(_safe_div(r.get("total_liab"), r.get("total_assets")))),
        },
    ]
    return {"periods": periods, "rows": rows}

# ------------------------
# API 路由接口
# ------------------------

@app.get("/api/finance/table")
def get_finance_table_api(
    ts_code: str = Query(..., description="股票代码，如 000001.SZ"),
    years: int = Query(6, ge=1, le=20, description="分析年限")
):
    try:
        payload = build_metrics_table(ts_code, years)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"内部计算错误: {exc}")

    if not payload["periods"]:
        raise HTTPException(status_code=404, detail="未找到财报数据，请确认股票代码是否正确")

    return {"code": 200, "message": "success", "data": payload}

@app.get("/api/sw_industry")
def get_sw_industry_api():
    industries = get_sw_industry()
    return {"code": 200, "message": "success", "data": [i.to_dict() for i in industries]}

@app.get("/api/stock_basic_all")
def get_stock_basic_all_api():
    stocks = get_stock_basic_all()
    return {"code": 200, "message": "success", "data": [i.to_dict() for i in stocks]}

@app.get("/api/index_member")
def get_index_member_api():
    members = get_index_member()
    return {"code": 200, "message": "success", "data": [i.to_dict() for i in members]}

@app.get("/api/company")
def get_company_api():
    companies = get_stock_company()
    return {"code": 200, "message": "success", "data": [i.to_dict() for i in companies]}

# ------------------------
# 启动配置
# ------------------------
if __name__ == "__main__":
    import uvicorn
    # 使用 uv run python main.py 启动或直接用 uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)