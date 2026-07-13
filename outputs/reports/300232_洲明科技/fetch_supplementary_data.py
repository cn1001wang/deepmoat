# -*- coding: utf-8 -*-
"""
洲明科技(300232.SZ) value-report 补充数据查询脚本（临时中间产物）
用途：用 tushare 补充分部收入、同行对比、质押、商誉、业绩预告等本地库未覆盖维度。
数据日期：2026-07-07
"""
import os, json, datetime
import pandas as pd
import tushare as ts

token = os.getenv("TUSHARE_TOKEN") or ts.get_token()
pro = ts.pro_api(token)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
def dump(name, df):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[saved] {path}  rows={len(df)}")

ZM = "300232.SZ"
PEERS = ["300232.SZ", "300296.SZ", "300389.SZ"]  # 洲明/利亚德/艾比森
PEER_NAMES = {"300232.SZ":"洲明科技","300296.SZ":"利亚德","300389.SZ":"艾比森"}

# 1) 分部收入（按产品 P / 按地区 D），取最近年报
for typ, tag in [("P","product"),("D","district")]:
    try:
        df = pro.mainbz(ts_code=ZM, type=typ, period="20251231")
        if df is None or df.empty:
            df = pro.mainbz(ts_code=ZM, type=typ, period="20241231")
        dump(f"mainbz_{tag}.csv", df)
        print(f"\n=== 分部({tag}) ===\n", df.to_string())
    except Exception as e:
        print(f"[mainbz {tag} 失败] {e}")

# 2) 同行最新估值 daily_basic
try:
    # 取最近交易日
    cal = pro.trade_cal(exchange="SSE", end_date="20260707", is_open="1")
    last_td = cal.sort_values("cal_date").iloc[-1]["cal_date"]
    df = pro.daily_basic(ts_code=",".join(PEERS), trade_date=last_td,
                         fields="ts_code,trade_date,close,pe,pb,ps,total_mv,circ_mv,dv_ratio")
    df["name"] = df["ts_code"].map(PEER_NAMES)
    dump(f"peers_daily_basic_{last_td}.csv", df)
    print(f"\n=== 同行估值 {last_td} ===\n", df.to_string())
except Exception as e:
    print(f"[daily_basic 失败] {e}")

# 3) 同行近5年 fina_indicator 关键指标
try:
    frames = []
    for code in PEERS:
        d = pro.fina_indicator(ts_code=code, start_date="20210101",
                               fields="ts_code,end_date,grossprofit_margin,netprofit_margin,roe,roic,debt_to_assets,q_profit_yoy,netprofit_margin,eps")
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["name"] = df["ts_code"].map(PEER_NAMES)
    dump("peers_fina_indicator_5y.csv", df)
    print("\n=== 同行财务指标近5年 ===\n", df.to_string())
except Exception as e:
    print(f"[fina_indicator 失败] {e}")

# 4) 洲明质押
try:
    df = pro.pledge_stat(ts_code=ZM)
    dump("pledge_stat.csv", df)
    print("\n=== 质押 ===\n", df.tail().to_string() if df is not None and not df.empty else "空")
except Exception as e:
    print(f"[pledge 失败] {e}")

# 5) 洲明商誉 + 关键资产负债项（用 balancesheet）
try:
    df = pro.balancesheet(ts_code=ZM, start_date="20210101",
                          fields="ts_code,end_date,goodwill,total_assets,total_liab,money_cap,accounts_rec,inventory,notes_payable,acct_payable,total_hldr_eqy_exc_min_int,st_borrow,lt_borrow")
    dump("balancesheet_key_5y.csv", df)
    print("\n=== 资产负债关键项 ===\n", df.to_string())
except Exception as e:
    print(f"[balancesheet 失败] {e}")

# 6) 业绩预告/快报
try:
    df = pro.forecast(ts_code=ZM, start_date="20250101")
    dump("forecast.csv", df)
    print("\n=== 业绩预告 ===\n", df.to_string() if df is not None and not df.empty else "空")
except Exception as e:
    print(f"[forecast 失败] {e}")
try:
    df = pro.express(ts_code=ZM, start_date="20250101")
    dump("express.csv", df)
    print("\n=== 业绩快报 ===\n", df.to_string() if df is not None and not df.empty else "空")
except Exception as e:
    print(f"[express 失败] {e}")

# 7) 近期公告
try:
    df = pro.anns_d(ts_code=ZM, start_date="20260101")
    dump("anns_2026.csv", df)
    print("\n=== 2026公告(前40) ===\n", df.head(40).to_string() if df is not None and not df.empty else "空")
except Exception as e:
    print(f"[anns 失败] {e}")

print("\nDONE")
