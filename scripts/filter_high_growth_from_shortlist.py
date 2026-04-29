"""
作用：
从已有低估值候选池 CSV 中再筛出高增长股票，
同时约束 ROE、估值、负债率和净现比，输出更聚焦的 shortlist。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从低估值候选池筛选高增长股票")
    parser.add_argument("input_csv", type=str, help="输入候选池 CSV 路径")
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/high-growth-20260415.csv",
        help="输出 CSV 路径",
    )
    parser.add_argument("--min-revenue-yoy", type=float, default=15.0)
    parser.add_argument("--min-profit-yoy", type=float, default=20.0)
    parser.add_argument("--min-roe", type=float, default=15.0)
    parser.add_argument("--max-pe", type=float, default=30.0)
    parser.add_argument("--max-debt-ratio", type=float, default=60.0)
    parser.add_argument("--min-ocf-profit", type=float, default=0.8)
    parser.add_argument("--topn", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_csv)
    output_path = Path(args.output)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    df = pd.read_csv(input_path)

    # 硬条件：增长 + 质量 + 不过贵
    picked = df[
        (df["revenue_yoy_pct"] >= args.min_revenue_yoy)
        & (df["profit_yoy_pct"] >= args.min_profit_yoy)
        & (df["roe_used"] >= args.min_roe)
        & (df["pe_ttm"] <= args.max_pe)
        & (df["debt_asset_ratio_pct"] <= args.max_debt_ratio)
        & (df["ocf_to_profit"] >= args.min_ocf_profit)
    ].copy()

    # 综合分：增长权重更高，兼顾 ROE 与估值
    picked["growth_score"] = (
        picked["revenue_yoy_pct"] * 0.45
        + picked["profit_yoy_pct"] * 0.45
        + picked["roe_used"] * 0.15
        - picked["pe_ttm"] * 0.15
    )
    picked = picked.sort_values(
        ["growth_score", "profit_yoy_pct", "revenue_yoy_pct"],
        ascending=[False, False, False],
    ).head(args.topn)

    cols = [
        "ts_code",
        "name",
        "industry",
        "trade_date",
        "market_cap_yi",
        "pe_ttm",
        "pb",
        "roe_used",
        "revenue_yoy_pct",
        "profit_yoy_pct",
        "debt_asset_ratio_pct",
        "net_margin_pct",
        "ocf_to_profit",
        "growth_score",
    ]
    picked = picked[cols]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    picked.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    print(f"入选数量: {len(picked)}")
    if not picked.empty:
        show_cols = [
            "ts_code",
            "name",
            "industry",
            "pe_ttm",
            "roe_used",
            "revenue_yoy_pct",
            "profit_yoy_pct",
            "growth_score",
        ]
        print(picked[show_cols].to_markdown(index=False))


if __name__ == "__main__":
    main()
