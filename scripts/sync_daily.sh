#!/usr/bin/env bash
set -euo pipefail

# 作用：执行每日增量同步任务。
# 适用场景：由 cron/launchd 等定时器在工作日晚上触发，也可以手动运行核查。

cd "$(dirname "$0")/.."

# 避免 macOS 定时任务里 uv 默认缓存目录权限异常；需要时可通过环境变量覆盖。
# 定时任务不依赖用户目录或仓库内遗留的 uv 缓存权限。
export UV_CACHE_DIR="${UV_CACHE_DIR:-"${TMPDIR:-/tmp}/deepmoat-uv-cache"}"
mkdir -p "${UV_CACHE_DIR}" logs

STATUS_PATH="$(pwd)/logs/sync_daily.status"
started_at="$(date '+%Y-%m-%dT%H:%M:%S%z')"

write_status() {
  local status="$1"
  local finished_at
  finished_at="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  printf 'status=%s\nstarted_at=%s\nfinished_at=%s\n' "${status}" "${started_at}" "${finished_at}" > "${STATUS_PATH}"
}

on_error() {
  write_status "failed"
}
trap on_error ERR

write_status "running"
uv run python -m app.worker.sync --daily
write_status "success"
trap - ERR
