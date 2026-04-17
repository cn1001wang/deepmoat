# Repo Agent Rules

## Skills Path Policy

- Always resolve project skills from repository-local `.agents/skills/`.
- Do not read project skills from global `~/.codex/skills/`.
- If a skill name exists in both places, always prefer the repository copy.

## Cross-Platform

- Keep all skill paths relative to the repository root.
- Avoid machine-specific absolute paths (for example `/Users/...` or `C:\Users\...`) in repo configs.
