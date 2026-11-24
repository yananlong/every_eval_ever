#!/bin/bash
# W5 arms in batches of 3 (12 cores) on the cores W3 leaves free; each arm through w5_run_entry.py (2 h cap per attempt).
T=/home/yananlong/every_eval_ever/eci_work/tools; V=/home/yananlong/every_eval_ever/eci_work/v11; L=$V/runs/logs
cd $V
for batch in "P8 PR J2" "P0 P0b P1" "P2 P4 P5" "P6 P7 X1" "X2"; do
  for n in $batch; do $T/eee_run.sh ../tools/w5_run_entry.py $n --draws 4000 > $L/eee_w5_$n.log 2>&1 & sleep 3; done
  wait
done
date -u +%FT%TZ > $V/runs/EEE/_w5_arms_end.txt
