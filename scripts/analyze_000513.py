import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:123456@localhost:5432/testdb')
# Convert SQLAlchemy URL to plain psycopg2 for pandas
DB_URL = DATABASE_URL.replace('+psycopg2', '')

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Stock code to analyze
ts_code = '000513.SZ'

print(f"Fetching fundamental data for {ts_code} (丽珠集团)...\n")

# 1. Income Statement (利润表)
query_income = text("""
    SELECT *
    FROM income
    WHERE ts_code = :ts_code AND report_type = '1'
    ORDER BY end_date DESC
    LIMIT 8
""")
df_income = pd.read_sql(query_income, engine, params={'ts_code': ts_code})
print(f"Income statements: {len(df_income)} records")

# 2. Balance Sheet (资产负债表)
query_balance = text("""
    SELECT *
    FROM balancesheet
    WHERE ts_code = :ts_code AND report_type = '1'
    ORDER BY end_date DESC
    LIMIT 8
""")
df_balance = pd.read_sql(query_balance, engine, params={'ts_code': ts_code})
print(f"Balance sheets: {len(df_balance)} records")

# 3. Cash Flow Statement (现金流量表)
query_cashflow = text("""
    SELECT *
    FROM cashflow
    WHERE ts_code = :ts_code AND report_type = '1'
    ORDER BY end_date DESC
    LIMIT 8
""")
df_cashflow = pd.read_sql(query_cashflow, engine, params={'ts_code': ts_code})
print(f"Cash flow statements: {len(df_cashflow)} records")

# 4. Financial Indicators (财务指标)
query_indicator = text("""
    SELECT *
    FROM fina_indicator
    WHERE ts_code = :ts_code
    ORDER BY end_date DESC
    LIMIT 8
""")
df_indicator = pd.read_sql(query_indicator, engine, params={'ts_code': ts_code})
print(f"Financial indicators: {len(df_indicator)} records")

# 5. Daily Basic (每日基本面数据, 最新)
query_daily = text("""
    SELECT *
    FROM daily_basic
    WHERE ts_code = :ts_code
    ORDER BY trade_date DESC
    LIMIT 1
""")
df_daily = pd.read_sql(query_daily, engine, params={'ts_code': ts_code})
print(f"Daily basic (latest): {len(df_daily)} record(s)")

# 6. Stock Basic Info
query_stock = text("""
    SELECT *
    FROM stock_basic
    WHERE ts_code = :ts_code
    LIMIT 1
""")
df_stock = pd.read_sql(query_stock, engine, params={'ts_code': ts_code})
print(f"Stock basic info: {len(df_stock)} record(s)")

print("\n" + "="*80)
print("LATEST PERIOD SUMMARY")
print("="*80)

if len(df_income) > 0:
    latest = df_income.iloc[0]
    print(f"\nReporting Period: {latest['end_date']}")
    print(f"Total Revenue: {latest['total_revenue']/1e8:.2f} 亿元" if latest['total_revenue'] else "N/A")
    print(f"Net Profit (归属母公司): {latest['n_income_attr_p']/1e8:.2f} 亿元" if latest['n_income_attr_p'] else "N/A")
    print(f"Basic EPS: {latest['basic_eps']:.4f}" if latest['basic_eps'] else "N/A")

if len(df_balance) > 0:
    latest_b = df_balance.iloc[0]
    print(f"\nTotal Assets: {latest_b['total_assets']/1e8:.2f} 亿元" if latest_b['total_assets'] else "N/A")
    print(f"Total Liabilities: {latest_b['total_liab']/1e8:.2f} 亿元" if latest_b['total_liab'] else "N/A")
    print(f"Shareholders Equity: {latest_b['total_hldr_eqy_inc_min_int']/1e8:.2f} 亿元" if latest_b['total_hldr_eqy_inc_min_int'] else "N/A")
    if latest_b['total_assets'] and latest_b['total_assets'] > 0:
        debt_ratio = latest_b['total_liab'] / latest_b['total_assets'] * 100
        print(f"Debt Ratio: {debt_ratio:.2f}%")

if len(df_cashflow) > 0:
    latest_c = df_cashflow.iloc[0]
    print(f"\nOperating Cash Flow: {latest_c['n_cashflow_act']/1e8:.2f} 亿元" if latest_c['n_cashflow_act'] else "N/A")
    print(f"Free Cash Flow: {latest_c['free_cashflow']/1e8:.2f} 亿元" if latest_c['free_cashflow'] else "N/A")

if len(df_indicator) > 0:
    latest_i = df_indicator.iloc[0]
    print(f"\nROE (加权平均): {latest_i['roe_waa']:.2f}%" if latest_i['roe_waa'] else "N/A")
    print(f"Gross Margin: {latest_i['grossprofit_margin']:.2f}%" if latest_i['grossprofit_margin'] else "N/A")
    print(f"Net Profit Margin: {latest_i['netprofit_margin']:.2f}%" if latest_i['netprofit_margin'] else "N/A")

if len(df_daily) > 0:
    latest_d = df_daily.iloc[0]
    print(f"\nTrade Date: {latest_d['trade_date']}")
    print(f"Close Price: {latest_d['close']:.2f}" if latest_d['close'] else "N/A")
    print(f"PE (TTM): {latest_d['pe_ttm']:.2f}" if latest_d['pe_ttm'] else "N/A")
    print(f"PB: {latest_d['pb']:.2f}" if latest_d['pb'] else "N/A")
    print(f"Total Market Value: {latest_d['total_mv']/10000:.2f} 亿元" if latest_d['total_mv'] else "N/A")

if len(df_stock) > 0:
    stock_info = df_stock.iloc[0]
    print(f"\nCompany Name: {stock_info['name']}")
    print(f"Industry: {stock_info['industry']}")
    print(f"Area: {stock_info['area']}")
    print(f"List Date: {stock_info['list_date']}")

# Save to CSV files in outputs directory
output_dir = Path(__file__).parent.parent / 'outputs'
output_dir.mkdir(exist_ok=True)

df_income.to_csv(output_dir / f'income_{ts_code}.csv', index=False, encoding='utf-8-sig')
df_balance.to_csv(output_dir / f'balance_{ts_code}.csv', index=False, encoding='utf-8-sig')
df_cashflow.to_csv(output_dir / f'cashflow_{ts_code}.csv', index=False, encoding='utf-8-sig')
df_indicator.to_csv(output_dir / f'indicator_{ts_code}.csv', index=False, encoding='utf-8-sig')
df_daily.to_csv(output_dir / f'daily_{ts_code}.csv', index=False, encoding='utf-8-sig')

print(f"\n[OK] Data saved to {output_dir}")

session.close()
