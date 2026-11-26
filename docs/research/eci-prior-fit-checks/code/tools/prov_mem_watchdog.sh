#!/usr/bin/env bash
# Host-side: every 15 s sum RSS of the PROV fit tree (run_prov.sh and descendants); SIGKILL the tree above 185 GiB (task cap 200 GiB in total); record peak; exit when run_prov.sh is gone.
LIMIT_KB=$((185 * 1024 * 1024)); PEAK=0
LOG=/home/yananlong/every_eval_ever/eci_work/v11/runs/logs/prov_mem_watchdog.log
desc() { local p; for p in $(pgrep -P "$1"); do echo "$p"; desc "$p"; done; }
sleep 15
while true; do
  root=$(pgrep -f "^bash .*run_prov.sh" | head -1)
  if [ -z "$root" ]; then echo "$(date -u +%FT%TZ) run_prov not running; exit; peak_kB=$PEAK" >> "$LOG"; exit 0; fi
  pids="$root $(desc "$root")"
  kb=$(ps -o rss= -p $(echo $pids | tr ' ' ',') 2>/dev/null | awk '{s+=$1} END {print s+0}')
  [ "$kb" -gt "$PEAK" ] && PEAK=$kb && echo "$(date -u +%FT%TZ) peak_kB=$PEAK" >> "$LOG"
  if [ "$kb" -gt "$LIMIT_KB" ]; then echo "$(date -u +%FT%TZ) RSS ${kb} > limit; kill tree" >> "$LOG"; sudo -n kill -9 $pids; exit 1; fi
  sleep 15
done
