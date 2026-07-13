# -*- coding: utf-8 -*-
"""修正草稿中分部图表的口径冲突：移除"LED光电行业"行业合计项，只保留产品分部。"""
import json, re
from pathlib import Path

draft = Path("outputs/reports/300232_洲明科技/value_300232_洲明科技_2607070928_draft.md")
text = draft.read_text(encoding="utf-8")

def repl(match):
    raw = match.group(1)
    try:
        opt = json.loads(raw)
    except Exception:
        return match.group(0)
    title = opt.get("title", {}).get("text", "")
    if "分产品收入结构" in title:
        for s in opt.get("series", []):
            if s.get("type") == "pie":
                s["data"] = [d for d in s.get("data", []) if d.get("name") != "LED光电行业"]
    elif "分产品收入变化" in title:
        opt["legend"]["data"] = [d for d in opt["legend"]["data"] if d != "LED光电行业"]
        opt["series"] = [s for s in opt.get("series", []) if s.get("name") != "LED光电行业"]
    elif "分产品利润结构" in title:
        xa = opt.get("xAxis", {})
        if isinstance(xa, dict) and "data" in xa:
            keep = [(i, v) for i, v in enumerate(xa["data"]) if v != "LED光电行业"]
            xa["data"] = [v for _, v in keep]
            for s in opt.get("series", []):
                if "data" in s:
                    s["data"] = [s["data"][i] for i, _ in keep]
    return "```json\n" + json.dumps(opt, ensure_ascii=False, indent=2) + "\n```"

new = re.sub(r"```json\n(.*?)\n```", repl, text, flags=re.DOTALL)
draft.write_text(new, encoding="utf-8")
print("草稿已修正")
