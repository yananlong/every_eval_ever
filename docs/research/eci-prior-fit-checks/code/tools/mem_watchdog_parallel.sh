#!/usr/bin/env bash
# Host-side: every 30 s, sum the RSS of the W3 process tree (w3_parallel.py and all descendants); SIGKILL the tree above the limit.
LIMIT_KB=$((200 * 1024 * 1024))
LOG=/home/yananlong/every_eval_ever/eci_work/v11/runs/logs/mem_watchdog_parallel.log
desc() { local p; for p in $(pgrep -P "$1"); do echo "$p"; desc "$p"; done; }
while true; do
  root=$(pgrep -f "^/opt/venvs/jax/bin/python runs/w3_parallel.py" | head -1)
  if [ -z "$root" ]; then echo "$(date -u +%FT%TZ) w3_parallel not running; watchdog exits" >> "$LOG"; exit 0; fi
  pids="$root $(desc "$root")"
  # w3_calibrate --one children use start_new_session, but stay descendants of the resume process
  kb=$(ps -o rss= -p $(echo $pids | tr ' ' ',') 2>/dev/null | awk '{s+=$1} END {print s+0}')
  if [ "$kb" -gt "$LIMIT_KB" ]; then
    echo "$(date -u +%FT%TZ) RSS ${kb} kB > limit; killing $pids" >> "$LOG"
    sudo -n kill -9 $pids
    exit 1
  fi
  sleep 30
done
