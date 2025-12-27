"""
财务 DataFrame / 数值工具函数
"""
import pandas as pd
from typing import List, Dict
from datetime import datetime
from app.utils.df_utils import dedup_finance_df
from app.utils.date_utils import generate_periods


def ensure_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["end_date"] + cols)

    df = dedup_finance_df(df)
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[["end_date"] + cols]


def filter_periods(df: pd.DataFrame, years: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    start_year = datetime.today().year - years + 1
    valid = set(generate_periods(start_year))
    latest = df["end_date"].max()

    result = df[df["end_date"].isin(valid)]
    if latest:
        result = pd.concat([result, df[df["end_date"] == latest]])

    return result.drop_duplicates("end_date").sort_values("end_date", ascending=False)


def merge_frames(frames: List[pd.DataFrame]) -> pd.DataFrame:
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()

    base = frames[0]
    for f in frames[1:]:
        base = pd.merge(base, f, on="end_date", how="outer")

    return base.sort_values("end_date", ascending=False)


def safe_div(a, b):
    if pd.isna(a) or pd.isna(b) or b == 0:
        return pd.NA
    return float(a) / float(b)


def yoy(data: Dict[str, float], md: str) -> Dict[str, float]:
    result = {}
    for k, v in data.items():
        if not k or len(k) != 8:
            result[k] = pd.NA
            continue
        year = int(k[:4])
        prev = data.get(f"{year - 1}{md}")
        result[k] = (v - prev) / prev if prev not in (None, 0) else pd.NA
    return result


def to_billion(val):
    return float(val) / 1e8 if not pd.isna(val) else None


def format_percent(val):
    return float(val) * 100 if val is not None and not pd.isna(val) else None
