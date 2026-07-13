# -*- coding: utf-8 -*-
"""本地库补充查询：同行估值、分部、审计意见、前十大股东、公司简介。"""
import os, pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:123456@localhost:5432/testdb").replace("+psycopg2","")
eng = create_engine(url)

def q(sql, **p):
    return pd.read_sql(text(sql), eng, params=p)

PEERS = ["300232.SZ","300296.SZ","300389.SZ"]
# 1) 同行最新估值 daily_basic
try:
    df = q("""
      SELECT d.ts_code, s.name, d.trade_date, d.close, d.pe, d.pe_ttm, d.pb, d.ps, d.ps_ttm,
             d.total_mv, d.circ_mv, d.dv_ratio, d.dv_ttm, d.turnover_rate
      FROM daily_basic d JOIN stock_basic s ON d.ts_code=s.ts_code
      WHERE d.ts_code IN :codes
      AND d.trade_date = (SELECT MAX(trade_date) FROM daily_basic WHERE ts_code=d.ts_code)
      ORDER BY d.ts_code
    """, codes=tuple(PEERS))
    print("=== 同行最新估值 ===")
    print(df.to_string())
    df.to_csv("outputs/reports/300232_洲明科技/peers_daily_basic_local.csv", index=False, encoding="utf-8-sig")
except Exception as e:
    print(f"[daily_basic 失败] {e}")
    # 兜底：分股票查最新
    try:
        rows=[]
        for c in PEERS:
            d = q("SELECT * FROM daily_basic WHERE ts_code=:c ORDER BY trade_date DESC LIMIT 1", c=c)
            rows.append(d)
        df=pd.concat(rows,ignore_index=True)
        print("=== 同行最新估值(兜底) ===")
        print(df.to_string())
        df.to_csv("outputs/reports/300232_洲明科技/peers_daily_basic_local.csv", index=False, encoding="utf-8-sig")
    except Exception as e2:
        print(f"[兜底失败] {e2}")

# 2) 表清单里找分部表
try:
    ins = inspect(eng)
    tables = ins.get_table_names()
    mbz = [t for t in tables if "mainbz" in t.lower() or "segment" in t.lower() or "main_bus" in t.lower()]
    print(f"\n=== 分部相关表: {mbz} ===")
    for t in mbz:
        d = q("SELECT * FROM :t LIMIT 1".replace(":t", t))
        print(t, list(d.columns))
        dd = q("SELECT * FROM "+t+" WHERE ts_code='300232.SZ' ORDER BY end_date DESC LIMIT 30")
        print(dd.to_string())
except Exception as e:
    print(f"[分部表失败] {e}")

# 3) 公司简介 stock_company
try:
    df = q("SELECT ts_code, name, introduction, main_business, business_scope FROM stock_company WHERE ts_code='300232.SZ'")
    print("\n=== 公司简介 ===")
    for c in df.columns:
        print(c, ":", str(df.iloc[0][c])[:600])
except Exception as e:
    print(f"[stock_company 失败] {e}")

# 4) 审计意见 fina_audit
try:
    df = q("SELECT * FROM fina_audit WHERE ts_code='300232.SZ' ORDER BY end_date DESC LIMIT 8")
    print("\n=== 审计意见 ===")
    print(df.to_string())
except Exception as e:
    print(f"[fina_audit 失败] {e}")

# 5) 前十大股东（如存在）
try:
    for t in ["stk_holdertrade","top10_holders","top10_floatholders"]:
        if t in tables:
            df = q(f"SELECT * FROM {t} WHERE ts_code='300232.SZ' ORDER BY end_date DESC LIMIT 20")
            print(f"\n=== {t} ===")
            print(df.to_string())
except Exception as e:
    print(f"[holders 失败] {e}")

print("\nDONE")
