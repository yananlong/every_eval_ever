#!/usr/bin/env bash
# usage: w5_runpy.sh <script> [args]  -- runs inside tpu-jupyter, CPU-only, 1 thread (4 chains = 4 procs per fit); cores via W5_CORES (default 0-191)
cd /home/yananlong/every_eval_ever/eci_work/v11
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/home/yananlong/every_eval_ever/eci_work/home
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export OMP_NUM_THREADS=${T:-1} OPENBLAS_NUM_THREADS=${T:-1} MKL_NUM_THREADS=${T:-1} NUMBA_NUM_THREADS=${T:-1}
exec taskset -c ${W5_CORES:-0-191} /opt/venvs/jax/bin/python "$@"
