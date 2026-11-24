#!/usr/bin/env bash
# Host-side: every 30 s sum RSS of the W4 process tree; SIGKILL above 200 GiB; record peak.
LIMIT_KB=$((200 * 1024 * 1024)); PEAK=0
LOG=/home/yananlong/every_eval_ever/eci_work/v11/runs/logs/mem_watchdog_w4.log
desc() { local p; for p in $(pgrep -P "$1"); do echo "$p"; desc "$p"; done; }
while true; do
  root=$(pgrep -f "^bash .*run_w4.sh" | head -1)
  if [ -z "$root" ]; then echo "$(date -u +%FT%TZ) run_w4 not running; exit; peak_kB=$PEAK" >> "$LOG"; exit 0; fi
  pids="$root $(desc "$root")"
  kb=$(ps -o rss= -p $(echo $pids | tr ' ' ',') 2>/dev/null | awk '{s+=$1} END {print s+0}')
  [ "$kb" -gt "$PEAK" ] && PEAK=$kb && echo "$(date -u +%FT%TZ) peak_kB=$PEAK" >> "$LOG"
  if [ "$kb" -gt "$LIMIT_KB" ]; then echo "$(date -u +%FT%TZ) RSS ${kb} > limit; kill" >> "$LOG"; sudo -n kill -9 $pids; exit 1; fi
  sleep 30
done
