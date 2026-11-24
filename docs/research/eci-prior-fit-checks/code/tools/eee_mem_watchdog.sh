#!/usr/bin/env bash
# Host-side: every 30 s sum RSS of all processes whose cwd is the EEE mirror; SIGKILL them above 120 GiB; record peak.
LIMIT_KB=$((120 * 1024 * 1024)); PEAK=0
LOG=/home/yananlong/every_eval_ever/eci_work/v11/runs/logs/eee_mem_watchdog.log
echo "$(date -u +%FT%TZ) start" >> "$LOG"
while true; do
  pids=""
  for p in $(pgrep -f "python" ); do c=$(readlink /proc/$p/cwd 2>/dev/null); case "$c" in *EEE/_mirror*) pids="$pids $p";; esac; done
  if [ -n "$pids" ]; then
    kb=$(ps -o rss= -p $(echo $pids | tr ' ' ',') 2>/dev/null | awk '{s+=$1} END {print s+0}')
    [ "$kb" -gt "$PEAK" ] && PEAK=$kb && echo "$(date -u +%FT%TZ) peak_kB=$PEAK nproc=$(echo $pids | wc -w)" >> "$LOG"
    if [ "$kb" -gt "$LIMIT_KB" ]; then echo "$(date -u +%FT%TZ) RSS ${kb} > limit; kill" >> "$LOG"; sudo -n kill -9 $pids; fi
  fi
  sleep 30
done
