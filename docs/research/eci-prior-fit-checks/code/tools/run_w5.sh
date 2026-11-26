#!/usr/bin/env bash
# Runs inside tpu-jupyter: W5 fits in parallel (4 chains each, 1 thread/proc), 2 h cap per fit attempt. usage: run_w5.sh DRAWS NAME...
cd /home/yananlong/every_eval_ever/eci_work/v11; mkdir -p runs/logs
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
DRAWS=$1; shift
echo "=== launch $(date -u +%FT%TZ) draws=$DRAWS names=$*" >> runs/logs/w5_launch.log
for n in "$@"; do
  taskset -c 0-191 /opt/venvs/jax/bin/python ../tools/w5_run_entry.py $n --draws $DRAWS > runs/logs/w5_$n.log 2>&1 &
  sleep 3   # stagger starts (numba/pytensor cache)
done
wait
echo "=== all done $(date -u +%FT%TZ)" >> runs/logs/w5_launch.log
