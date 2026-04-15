import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
db = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:123456@localhost:5432/testdb').replace('+psycopg2','')
engine = create_engine(db)

sql = """
SELECT end_date, total_revenue, oper_cost, n_income_attr_p, operate_profit
FROM income
WHERE ts_code='300274.SZ' AND report_type='1' AND end_date IN ('20251231','20250930','20241231','20240930')
ORDER BY end_date DESC
"""

df = pd.read_sql(text(sql), engine)
row = {r['end_date']: r for _, r in df.iterrows()}


def q4(full, q3):
    return float(full) - float(q3)

def margin(v, r):
    return v / r * 100

r25 = q4(row['20251231']['total_revenue'], row['20250930']['total_revenue'])
oc25 = q4(row['20251231']['oper_cost'], row['20250930']['oper_cost'])
np25 = q4(row['20251231']['n_income_attr_p'], row['20250930']['n_income_attr_p'])
op25 = q4(row['20251231']['operate_profit'], row['20250930']['operate_profit'])

r24 = q4(row['20241231']['total_revenue'], row['20240930']['total_revenue'])
oc24 = q4(row['20241231']['oper_cost'], row['20240930']['oper_cost'])
np24 = q4(row['20241231']['n_income_attr_p'], row['20240930']['n_income_attr_p'])
op24 = q4(row['20241231']['operate_profit'], row['20240930']['operate_profit'])

print('Q4_2025_revenue_yi', round(r25/1e8,2))
print('Q4_2025_gross_margin_pct', round(margin(r25-oc25, r25),2))
print('Q4_2025_operating_margin_pct', round(margin(op25, r25),2))
print('Q4_2025_net_margin_pct', round(margin(np25, r25),2))
print('Q4_2025_net_profit_yi', round(np25/1e8,2))

print('Q4_2024_revenue_yi', round(r24/1e8,2))
print('Q4_2024_gross_margin_pct', round(margin(r24-oc24, r24),2))
print('Q4_2024_operating_margin_pct', round(margin(op24, r24),2))
print('Q4_2024_net_margin_pct', round(margin(np24, r24),2))
print('Q4_2024_net_profit_yi', round(np24/1e8,2))

print('Q4_revenue_yoy_pct', round((r25-r24)/r24*100,2))
print('Q4_net_profit_yoy_pct', round((np25-np24)/np24*100,2))
