#!/usr/bin/env bash
set -euo pipefail

# 作用：执行每日增量同步任务。
# 适用场景：由 cron/launchd 等定时器在工作日晚上触发，也可以手动运行核查。

cd "$(dirname "$0")/.."

# 避免 macOS 定时任务里 uv 默认缓存目录权限异常；需要时可通过环境变量覆盖。
export UV_CACHE_DIR="${UV_CACHE_DIR:-"$(pwd)/.cache/uv"}"
mkdir -p "${UV_CACHE_DIR}" logs

uv run python -m app.worker.sync --daily
