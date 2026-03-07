# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Goals
- Prioritize the minimum number of tokens that still capture intent; favor concise responses and code, generating outputs as fast as possible.
- When creating Python code, always place it under `./scripts/`, run it locally, and confirm execution succeeded.
- If a task asks for a particular stock endpoint (e.g., `http://localhost:5100/stock/000592.SZ`), save the response payload into `./outputs/` and tell the user where that file lives.
- The README (`README.md` and `fe/README.md`) contains the high-level domain narrative (FastAPI + Vue stack, Morningstar-style moat evaluations); reference it for background instead of repeating details unnecessarily.

## Common commands
- Backend
  ```bash
  python -m venv .venv
  .venv\Scripts\activate.bat   # Windows
  source .venv/bin/activate     # Unix
  uv sync
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- Worker sync
  ```bash
  uv run python -m app.worker.sync --daily
  # other flags are defined in app/worker/sync.py
  ```
- Frontend (inside `fe/`)
  ```bash
  pnpm install
  pnpm dev
  pnpm build
  pnpm preview
  ```

## Architecture snapshot
- **Backend**: FastAPI app with routers in `app/api/v1/`, services in `app/service/`, SQLAlchemy models in `app/models/models.py`, CRUD helpers under `app/crud/`, and a data sync worker at `app/worker/sync.py`. Settings live in `app/config.py` and load `.env` (DATABASE_URL, TUSHARE_TOKEN).
- **Database schema**: Primary definitions reside in `app/models/models.py` (income, balance_sheet, cash_flow, daily_basic, fina_indicator, etc.). Refer to this file first to understand table columns and data types before querying.
- **Frontend**: Vue 3 + TypeScript located in `fe/src/` (views, components, router). Tooling is powered by Vite, UnoCSS, Pinia, Element Plus, and AG Grid; package scripts are in `fe/package.json`.

## Data and analysis protocol
- When a request touches database data, merge three-statement tables (`income`, `balance_sheet`, `cash_flow`) plus `daily_basic`; then enrich with the latest public data via web search so the fundamental analysis reflects the current macro/industry context.
- Start from `app/models/models.py` to understand the column names, then leverage CRUD/service helpers in `app/crud/` and `app/service/` (using `trend_service`, `finance_service`, etc.) to fetch and process records.
- If the user specifies filters (e.g., ROE > 12%, debt ratio < 40%), apply them directly against the parsed records before producing insights. Always return a full fundamental analysis report summarizing valuation metrics, growth trends, profitability, and risk factors.

## Outputs and reminders
- Always mention the database definition file path (`app/models/models.py`) when clarifying how you access tables so future AI instances don't re-search for it.
- Combine `daily_basic` with the three statements to describe liquidity, solvency, and profitability; include ratios (ROE, ROA, debt/assets) and highlight any major deviations from historical patterns.
- When interfacing with `http://localhost:5100/stock/000592.SZ`, store the fetched JSON/text in `./outputs/stock-000592-SZ.json` (or similar) and notify the user of the saved file path in your response.
- Always consult the README for domain context rather than inventing new background sections.
- 最后生成的报告使用中文输出
