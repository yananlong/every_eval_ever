#!/usr/bin/env bash
# Runs inside tpu-jupyter: refit missing converged G-null replicates, 1 thread per process, 4 chains each
cd /home/yananlong/every_eval_ever/eci_work/v11; mkdir -p runs/logs
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "=== launch $(date -u +%FT%TZ)" >> runs/logs/w4d_refit.log
taskset -c 0-191 /opt/venvs/jax/bin/python ../tools/w4d_refit_driver.py ${1:-44} >> runs/logs/w4d_refit.log 2>&1
