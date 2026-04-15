#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SVG_W = 1200
SVG_H = 720
COLORS = [
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
]


@dataclass
class ChartBlock:
    index: int
    heading: str
    option: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把 value report 草稿中的 ECharts option 渲染为 SVG 图片")
    parser.add_argument("draft_markdown", help="草稿 Markdown 文件路径")
    parser.add_argument(
        "--output-dir",
        default="",
        help="图表输出目录（默认 outputs/charts/<草稿文件名去掉_draft>）",
    )
    parser.add_argument(
        "--inject-report",
        default="",
        help="将图片片段插入到目标报告 markdown（会写入标记区间）",
    )
    return parser.parse_args()


def parse_blocks(md_text: str) -> list[ChartBlock]:
    pattern = re.compile(r"^###\s+(\d+)\.\s+([^\n]+)\n```json\n(.*?)\n```", re.MULTILINE | re.DOTALL)
    blocks: list[ChartBlock] = []
    for m in pattern.finditer(md_text):
        idx = int(m.group(1))
        heading = m.group(2).strip()
        raw = m.group(3).strip()
        try:
            option = json.loads(raw)
        except json.JSONDecodeError:
            continue
        blocks.append(ChartBlock(index=idx, heading=heading, option=option))
    return blocks


def series_values(series: dict[str, Any]) -> list[float]:
    out: list[float] = []
    for v in series.get("data", []):
        if isinstance(v, dict):
            v = v.get("value")
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(0.0)
    return out


def svg_header(title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="40" y="42" font-size="26" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#222">{escape(title)}</text>',
    ]


def draw_legend(lines: list[str], labels: list[str]) -> None:
    x0 = 40
    y0 = 72
    step = 170
    for i, label in enumerate(labels):
        color = COLORS[i % len(COLORS)]
        x = x0 + i * step
        lines.append(f'<rect x="{x}" y="{y0 - 12}" width="22" height="10" fill="{color}"/>')
        lines.append(
            f'<text x="{x + 28}" y="{y0 - 2}" font-size="16" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#333">{escape(label)}</text>'
        )


def render_bar_line(option: dict[str, Any], title: str, output_path: Path) -> None:
    lines = svg_header(title)
    x_data = option.get("xAxis", {}).get("data", [])
    if not x_data:
        x_data = [str(i + 1) for i in range(max(1, len(option.get("series", []))))]

    series = option.get("series", [])
    labels = [str(s.get("name", f"S{i+1}")) for i, s in enumerate(series)]
    draw_legend(lines, labels)

    left, right = 90, 70
    top, bottom = 130, 90
    plot_w = SVG_W - left - right
    plot_h = SVG_H - top - bottom

    all_vals: list[float] = []
    normalized_series: list[tuple[dict[str, Any], list[float]]] = []
    for s in series:
        vals = series_values(s)
        if len(vals) < len(x_data):
            vals += [0.0] * (len(x_data) - len(vals))
        normalized_series.append((s, vals[: len(x_data)]))
        all_vals.extend(vals[: len(x_data)])

    if not all_vals:
        all_vals = [0.0]
    y_min = min(0.0, min(all_vals))
    y_max = max(0.0, max(all_vals))
    if abs(y_max - y_min) < 1e-9:
        y_max = y_min + 1.0

    def y_to_px(v: float) -> float:
        return top + (y_max - v) / (y_max - y_min) * plot_h

    # Axes
    x_axis_y = y_to_px(0.0)
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#555" stroke-width="1"/>')
    lines.append(f'<line x1="{left}" y1="{x_axis_y}" x2="{left + plot_w}" y2="{x_axis_y}" stroke="#555" stroke-width="1"/>')

    # Grid + y ticks
    tick_n = 5
    for i in range(tick_n + 1):
        v = y_min + (y_max - y_min) * i / tick_n
        y = y_to_px(v)
        lines.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#eee" stroke-width="1"/>')
        lines.append(
            f'<text x="{left - 12}" y="{y + 5}" text-anchor="end" font-size="14" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#666">{v:.2f}</text>'
        )

    count = len(x_data)
    step = plot_w / max(1, count)
    bar_series = [pair for pair in normalized_series if str(pair[0].get("type", "line")).lower() == "bar"]
    line_series = [pair for pair in normalized_series if str(pair[0].get("type", "line")).lower() != "bar"]

    # X labels
    for i, label in enumerate(x_data):
        x = left + (i + 0.5) * step
        lines.append(
            f'<text x="{x}" y="{top + plot_h + 28}" text-anchor="middle" font-size="14" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#666">{escape(str(label))}</text>'
        )

    # Bars
    bar_width = step * 0.68 / max(1, len(bar_series)) if bar_series else 0
    for s_idx, (s, vals) in enumerate(bar_series):
        color = COLORS[s_idx % len(COLORS)]
        for i, v in enumerate(vals):
            x_center = left + (i + 0.5) * step
            x = x_center - (len(bar_series) * bar_width) / 2 + s_idx * bar_width
            y = y_to_px(v)
            h = abs(x_axis_y - y)
            y_rect = min(y, x_axis_y)
            lines.append(f'<rect x="{x:.2f}" y="{y_rect:.2f}" width="{bar_width * 0.92:.2f}" height="{h:.2f}" fill="{color}" opacity="0.85"/>')

    # Lines
    offset = len(bar_series)
    for l_idx, (_s, vals) in enumerate(line_series):
        color = COLORS[(offset + l_idx) % len(COLORS)]
        points = []
        for i, v in enumerate(vals):
            x = left + (i + 0.5) * step
            y = y_to_px(v)
            points.append((x, y))
        if not points:
            continue
        poly = " ".join([f"{x:.2f},{y:.2f}" for x, y in points])
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{poly}"/>')
        for x, y in points:
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def pie_slice_path(cx: float, cy: float, r: float, start_angle: float, end_angle: float) -> str:
    x1 = cx + r * math.cos(start_angle)
    y1 = cy + r * math.sin(start_angle)
    x2 = cx + r * math.cos(end_angle)
    y2 = cy + r * math.sin(end_angle)
    large_arc = 1 if (end_angle - start_angle) > math.pi else 0
    return (
        f"M {cx:.2f} {cy:.2f} "
        f"L {x1:.2f} {y1:.2f} "
        f"A {r:.2f} {r:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z"
    )


def render_pie(option: dict[str, Any], title: str, output_path: Path) -> None:
    lines = svg_header(title)
    series = option.get("series", [])
    data = []
    if series:
        data = series[0].get("data", [])
    cleaned: list[tuple[str, float]] = []
    for item in data:
        if isinstance(item, dict):
            name = str(item.get("name", "N/A"))
            val = item.get("value", 0)
        else:
            name = "N/A"
            val = item
        try:
            value = max(0.0, float(val))
        except (TypeError, ValueError):
            value = 0.0
        cleaned.append((name, value))

    total = sum(v for _, v in cleaned)
    if total <= 0:
        lines.append(
            '<text x="40" y="120" font-size="20" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#777">无有效数据可绘制</text>'
        )
        lines.append("</svg>")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return

    cx, cy, r = 380, 390, 220
    angle = -math.pi / 2
    for i, (name, value) in enumerate(cleaned):
        frac = value / total
        next_angle = angle + frac * 2 * math.pi
        color = COLORS[i % len(COLORS)]
        path = pie_slice_path(cx, cy, r, angle, next_angle)
        lines.append(f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="1"/>')
        angle = next_angle

    # Legend
    x0, y0 = 700, 190
    for i, (name, value) in enumerate(cleaned):
        color = COLORS[i % len(COLORS)]
        y = y0 + i * 30
        pct = value / total * 100
        lines.append(f'<rect x="{x0}" y="{y - 11}" width="20" height="12" fill="{color}"/>')
        lines.append(
            f'<text x="{x0 + 28}" y="{y}" font-size="14" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" fill="#333">{escape(name)}  {value:.2f} ({pct:.1f}%)</text>'
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def render_chart(block: ChartBlock, output_path: Path) -> None:
    series = block.option.get("series", [])
    if series and str(series[0].get("type", "")).lower() == "pie":
        render_pie(block.option, block.heading, output_path)
        return
    render_bar_line(block.option, block.heading, output_path)


def build_snippet(blocks: list[ChartBlock], chart_paths: list[Path]) -> str:
    lines = ["## 图表图片（自动生成）", ""]
    for block, path in zip(blocks, chart_paths):
        lines.append(f"### {block.index}. {block.heading}")
        lines.append(f"![{block.heading}]({path.resolve()})")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def inject_snippet(target_path: Path, snippet: str) -> None:
    start_marker = "<!-- VALUE_CHARTS_START -->"
    end_marker = "<!-- VALUE_CHARTS_END -->"
    payload = f"{start_marker}\n{snippet}{end_marker}\n"
    text = target_path.read_text(encoding="utf-8")
    if start_marker in text and end_marker in text:
        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
        text = pattern.sub(payload.strip(), text)
    else:
        text = text.rstrip() + "\n\n" + payload
    target_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    draft_path = Path(args.draft_markdown)
    if not draft_path.is_absolute():
        draft_path = ROOT / draft_path
    text = draft_path.read_text(encoding="utf-8")
    blocks = parse_blocks(text)
    if not blocks:
        raise SystemExit("未找到可解析的图表 JSON 代码块")

    if args.output_dir:
        out_dir = Path(args.output_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
    else:
        stem = draft_path.stem.replace("_draft", "")
        out_dir = ROOT / "outputs" / "charts" / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_paths: list[Path] = []
    for i, block in enumerate(blocks, start=1):
        path = out_dir / f"chart_{i:02d}.svg"
        render_chart(block, path)
        chart_paths.append(path)

    snippet = build_snippet(blocks, chart_paths)
    snippet_path = out_dir / "charts_snippet.md"
    snippet_path.write_text(snippet, encoding="utf-8")

    print(f"草稿: {draft_path}")
    print(f"图表输出目录: {out_dir}")
    print(f"图表数量: {len(chart_paths)}")
    print(f"片段文件: {snippet_path}")

    if args.inject_report:
        target = Path(args.inject_report)
        if not target.is_absolute():
            target = ROOT / target
        inject_snippet(target, snippet)
        print(f"已插入图表片段到: {target}")


if __name__ == "__main__":
    main()
