#!/usr/bin/env bash
# Host-side: run a python script in tpu-jupyter, CPU only, cores 0-63, 1 thread.  usage: bsel_py.sh <script> [args]
exec sudo -n docker exec -u 2001:2001 -w /home/yananlong/every_eval_ever/eci_work/v11 -e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/tmp \
  -e PYTHONPATH=/home/yananlong/every_eval_ever/eci_work/v11/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1 \
  tpu-jupyter taskset -c 0-63 /opt/venvs/jax/bin/python -W ignore "$@"
