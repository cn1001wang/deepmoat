#!/usr/bin/env bash
set -euo pipefail

# 作用：把每日同步任务安装到当前用户 crontab。
# 适用场景：在部署机器上运行一次，让任务每个工作日 20:00 自动执行。

cd "$(dirname "$0")/.."

REPO_ROOT="$(pwd)"
SCRIPT_PATH="${REPO_ROOT}/scripts/sync_daily.sh"
LOG_PATH="${REPO_ROOT}/logs/sync_daily.log"
MARKER_BEGIN="# deepmoat daily sync begin"
MARKER_END="# deepmoat daily sync end"
CRON_LINE="0 20 * * 1-5 cd '${REPO_ROOT}' && '${SCRIPT_PATH}' >> '${LOG_PATH}' 2>&1"

if ! command -v crontab >/dev/null 2>&1; then
  echo "未找到 crontab 命令，请先安装或改用系统定时器。"
  exit 1
fi

chmod +x "${SCRIPT_PATH}"
mkdir -p "${REPO_ROOT}/logs"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"

{
  printf '%s\n' "${CURRENT_CRON}" | awk -v begin="${MARKER_BEGIN}" -v end="${MARKER_END}" '
    $0 == begin { skip = 1; next }
    $0 == end { skip = 0; next }
    skip != 1 { print }
  ' | sed '/^[[:space:]]*$/N;/^\n$/D'
  printf '%s\n' "${MARKER_BEGIN}"
  printf '%s\n' "${CRON_LINE}"
  printf '%s\n' "${MARKER_END}"
} | crontab -

echo "已安装定时任务：每个工作日 20:00 执行 ${SCRIPT_PATH}"
echo "日志文件：${LOG_PATH}"
