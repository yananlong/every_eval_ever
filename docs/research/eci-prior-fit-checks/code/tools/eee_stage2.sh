#!/bin/bash
# After W3 on the EEE input: W3M, W4 (+fold prefits), W4d, figures data, anchors extension, and the W5 arms, in parallel.
# Host-side launcher; every python runs in the container from the EEE mirror root through eee_run.sh (cores 72-191, 1 thread).
T=/home/yananlong/every_eval_ever/eci_work/tools; V=/home/yananlong/every_eval_ever/eci_work/v11; L=$V/runs/logs; E=$V/runs/EEE
cd $V
echo "=== stage2 launch $(date -u +%FT%TZ)" >> $L/eee_stage2.log
# --- W5 arms: launched earlier in batches on spare cores (eee_w5_batches.sh)
# --- W4: ppc with fold prefits
( rm -f $E/W4/folds.csv
  $T/eee_run.sh runs/w4_ppc.py > $L/eee_w4_ppc.log 2>&1 &
  main=$!
  ( while [ ! -s $E/W4/folds.csv ]; do sleep 5; done; sleep 20
    for f in 1 2 3 4; do $T/eee_run.sh ../tools/w4_prefit_fold.py $f > $L/eee_w4_prefit_fold$f.log 2>&1 & sleep 3; done; wait ) &
  wait $main; echo "=== w4_ppc exit $? $(date -u +%FT%TZ)" >> $L/eee_stage2.log; wait
  $T/eee_run.sh ../tools/w4_localise.py > $L/eee_w4_localise.log 2>&1
  $T/eee_run.sh ../tools/w4d_step1.py > $L/eee_w4d_step1.log 2>&1
  $T/eee_run.sh ../tools/w4d_deletion.py > $L/eee_w4d_deletion.log 2>&1
  $T/eee_run.sh ../tools/fig_misspec_data.py > $L/eee_fig_misspec.log 2>&1
  $T/eee_run.sh ../tools/fig_structure_data.py > $L/eee_fig_structure.log 2>&1
  $T/eee_run.sh runs/w4_graphics.py > $L/eee_w4_graphics.log 2>&1
  echo "=== W4 chain done $(date -u +%FT%TZ)" >> $L/eee_stage2.log ) &
# --- W3M full (Modrak-style rank tests on all converged nulls)
( $T/eee_run.sh ../tools/w3m_full.py --procs 20 > $L/eee_w3m_full.log 2>&1
  $T/eee_run.sh ../tools/eee_w3m_full_analyze.py > $L/eee_w3m_analyze.log 2>&1
  $T/eee_run.sh ../tools/eee_w3m_full_chartdata.py > $L/eee_w3m_chartdata.log 2>&1
  echo "=== W3M done $(date -u +%FT%TZ)" >> $L/eee_stage2.log ) &
# --- anchors extension (post-processing)
( CR=$(cd $E/W3/rep; for r in $(seq 0 19); do [ -f 2d_$r.json ] || { grep -qi "anchor" 2d_$r.log 2>/dev/null && echo -n "$r,"; }; done)
  sudo -n docker exec -u 2001:2001 -w $E/_mirror/v11 -e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/tmp -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1 -e EEE_CRASHED_2D="${CR%,}" \
    -e PYTHONPATH=$V/runs/vendor/eci-public/src tpu-jupyter taskset -c 72-191 /opt/venvs/jax/bin/python ../tools/eee_wa_extend.py > $L/eee_wa_extend.log 2>&1
  echo "=== WA ext done (crashed 2d: ${CR%,}) $(date -u +%FT%TZ)" >> $L/eee_stage2.log ) &
wait
echo "=== stage2 all done $(date -u +%FT%TZ)" >> $L/eee_stage2.log
