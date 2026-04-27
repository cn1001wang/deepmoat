#!/usr/bin/env python3
"""
作用：
把项目技能统一映射到仓库内 `.agents/skills/`，避免不同机器误用全局技能目录。
适合在新机器初始化仓库，或修复技能解析路径混乱时使用。

What this script does:
1. Creates/updates local mapping files for supported clients:
   - .claude/skills/<skill-name>
   - .trae/skills/<skill-name>
   - .codex/skills/<skill-name>
   Each file points to ../../.agents/skills/<skill-name>
2. Optionally removes duplicated project skills from ~/.codex/skills
   to avoid global-path ambiguity.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CLIENT_SKILLS_DIRS = [
    (".claude", "skills"),
    (".trae", "skills"),
    (".codex", "skills"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def list_repo_skill_names(root: Path) -> list[str]:
    skills_root = root / ".agents" / "skills"
    if not skills_root.exists():
        raise FileNotFoundError(f"Missing skills directory: {skills_root}")
    return sorted([p.name for p in skills_root.iterdir() if p.is_dir()])


def write_local_mappings(root: Path, skill_names: list[str]) -> None:
    for client_dir, skills_dir in CLIENT_SKILLS_DIRS:
        out_dir = root / client_dir / skills_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        for skill in skill_names:
            mapping_file = out_dir / skill
            mapping_file.write_text(f"../../.agents/skills/{skill}\n", encoding="utf-8")


def purge_global_duplicates(skill_names: list[str]) -> list[Path]:
    removed: list[Path] = []
    global_skills_root = Path.home() / ".codex" / "skills"
    if not global_skills_root.exists():
        return removed

    for skill in skill_names:
        target = global_skills_root / skill
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure repo-local skill mapping.")
    parser.add_argument(
        "--purge-global",
        action="store_true",
        help="Remove duplicated project skills from ~/.codex/skills",
    )
    args = parser.parse_args()

    root = repo_root()
    skill_names = list_repo_skill_names(root)

    write_local_mappings(root, skill_names)
    print(f"[OK] Wrote local mappings for {len(skill_names)} skills from {root / '.agents' / 'skills'}")

    if args.purge_global:
        removed = purge_global_duplicates(skill_names)
        if removed:
            print("[OK] Removed duplicated global skills:")
            for p in removed:
                print(f"  - {p}")
        else:
            print("[OK] No duplicated global skills found under ~/.codex/skills")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
