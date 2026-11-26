#!/usr/bin/env bash
# Runs inside tpu-jupyter: W4 (w4_ppc then w4_graphics), CPU-only, cores 0-191.
# w4_ppc.py fits its 5 held-out folds sequentially; once it has written folds.csv, folds 1-4 are pre-fitted
# concurrently (one process each, same fit call) and w4_ppc.py skips them through the sidecar match.
set -uo pipefail
cd /home/yananlong/every_eval_ever/eci_work/v11
mkdir -p runs/logs
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMBA_NUM_THREADS=8
PY=/opt/venvs/jax/bin/python
rm -f runs/W/W4/folds.csv
echo "=== launch $(date -u +%FT%TZ) pid $$" >> runs/logs/w4_ppc.log
taskset -c 0-191 $PY runs/w4_ppc.py >> runs/logs/w4_ppc.log 2>&1 &
main=$!
( while [ ! -s runs/W/W4/folds.csv ]; do sleep 5; done; sleep 20
  for f in 1 2 3 4; do taskset -c 0-191 $PY ../tools/w4_prefit_fold.py $f >> runs/logs/w4_prefit_fold$f.log 2>&1 & sleep 3; done; wait ) &
wait $main; rc=$?
echo "=== w4_ppc exit $rc $(date -u +%FT%TZ)" >> runs/logs/w4_ppc.log
wait
[ $rc -eq 0 ] || exit $rc
echo "=== launch $(date -u +%FT%TZ)" >> runs/logs/w4_graphics.log
taskset -c 0-191 $PY runs/w4_graphics.py >> runs/logs/w4_graphics.log 2>&1
echo "=== w4_graphics exit $? $(date -u +%FT%TZ)" >> runs/logs/w4_graphics.log
