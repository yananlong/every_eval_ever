#!/usr/bin/env bash
# usage: w4d_runpy.sh <script> [args]  -- runs inside tpu-jupyter, CPU-only, 8 threads
cd /home/yananlong/every_eval_ever/eci_work/v11
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=${T:-8} OPENBLAS_NUM_THREADS=${T:-8} MKL_NUM_THREADS=${T:-8} NUMBA_NUM_THREADS=${T:-8}
exec taskset -c 0-191 /opt/venvs/jax/bin/python "$@"
