#!/bin/bash
# Wait for the W2 prefits, then W2 summary, W3 positive control and the W3 parallel driver (host-side launcher).
T=/home/yananlong/every_eval_ever/eci_work/tools; V=/home/yananlong/every_eval_ever/eci_work/v11; L=$V/runs/logs; E=$V/runs/EEE
cd $V
until [ -s $E/W2/seed12345.json ] && [ -s $E/W2/seed22345.json ] && [ -s $E/W2/seed32345.json ]; do sleep 10; done
date -u +%FT%TZ > $E/_w3_start.txt
( until [ -s $E/W2/f0_seed12345.json ] && [ -s $E/W2/f0_seed22345.json ] && [ -s $E/W2/loader_input.json ]; do sleep 10; done
  $T/eee_run.sh runs/w2_fit.py > $L/eee_w2_fit.log 2>&1
  $T/eee_run.sh runs/wa_anchor_select.py > $L/eee_wa_select.log 2>&1; $T/eee_run.sh runs/wa_anchor.py > $L/eee_wa_anchor.log 2>&1
  $T/eee_run.sh ../tools/w5_agg.py --s5-only > $L/eee_w5_s5.log 2>&1 ) &
$T/eee_run.sh runs/w3_resume.py --stage pc > $L/eee_w3_pc.log 2>&1 &
sleep 20
$T/eee_run.sh runs/w3_parallel.py --workers 27 > $L/eee_w3_parallel.log 2>&1
wait
date -u +%FT%TZ > $E/_w3_end.txt
