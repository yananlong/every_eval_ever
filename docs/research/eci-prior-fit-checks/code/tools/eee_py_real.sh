#!/bin/bash
# python in the container from the REAL v11 root (read-only use of runs/W; writes only under runs/EEE)
exec sudo -n docker exec -u 2001:2001 -w /home/yananlong/every_eval_ever/eci_work/v11 -e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/tmp -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1 \
 -e PYTHONPATH=/home/yananlong/every_eval_ever/eci_work/v11/runs/vendor/eci-public/src tpu-jupyter taskset -c 72-191 /opt/venvs/jax/bin/python "$@"
