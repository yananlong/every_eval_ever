#!/usr/bin/env bash
# Runs inside tpu-jupyter (as the host user): W3 resume pinned to cores 0-191, CPU-only JAX, capped BLAS/Numba threads.
set -uo pipefail
cd /home/yananlong/every_eval_ever/eci_work/v11
mkdir -p runs/logs
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=4
mkdir -p "$HOME"
echo "=== launch $(date -u +%FT%TZ) pid $$" >> runs/logs/w3_resume.log
exec taskset -c 0-191 /opt/venvs/jax/bin/python runs/w3_resume.py "$@" >> runs/logs/w3_resume.log 2>&1
