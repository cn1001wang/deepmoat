#!/usr/bin/env bash
set -euo pipefail

# 作用：补齐 daily_basic 历史数据。
# 默认近 3 年逐日同步；3 年以前从 2016-01-01 开始按月末附近窗口抽样。
# 可通过 DAILY_START_DATE / DAILY_END_DATE / DAILY_RECENT_YEARS /
# DAILY_SAMPLE_WINDOW_DAYS 覆盖。

cd "$(dirname "$0")/.."

DAILY_START_DATE="${DAILY_START_DATE:-20160101}"
DAILY_RECENT_YEARS="${DAILY_RECENT_YEARS:-3}"
DAILY_SAMPLE_WINDOW_DAYS="${DAILY_SAMPLE_WINDOW_DAYS:-7}"

# 避免 macOS 定时任务里 uv 默认缓存目录权限异常；需要时可通过环境变量覆盖。
export UV_CACHE_DIR="${UV_CACHE_DIR:-"$(pwd)/.cache/uv"}"
mkdir -p "${UV_CACHE_DIR}" logs

args=(
  --daily
  --daily_hybrid
  --daily_start_date "${DAILY_START_DATE}"
  --daily_recent_years "${DAILY_RECENT_YEARS}"
  --daily_sample_window_days "${DAILY_SAMPLE_WINDOW_DAYS}"
)

if [[ -n "${DAILY_END_DATE:-}" ]]; then
  args+=(--daily_end_date "${DAILY_END_DATE}")
fi

uv run python -m app.worker.sync "${args[@]}"
