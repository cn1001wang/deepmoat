#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

WORKERS="${SYNC_WORKERS:-1}"
MAINBZ_TYPES="${SYNC_MAINBZ_TYPES:-P,D,I}"

# Avoid macOS permission issues with uv's default cache under ~/.cache by
# defaulting to a repo-local cache directory (override with UV_CACHE_DIR).
export UV_CACHE_DIR="${UV_CACHE_DIR:-"$(pwd)/.cache/uv"}"
mkdir -p "${UV_CACHE_DIR}"

uv run python -m app.worker.sync \
  --stock_basic \
  --stock_company \
  --industry \
  --index_member \
  --daily \
  --finance \
  --fina_indicator \
  --dividend \
  --fina_audit \
  --fina_mainbz \
  --mainbz_types "${MAINBZ_TYPES}" \
  --workers "${WORKERS}"
