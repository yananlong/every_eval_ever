#!/bin/bash
# Run a python script inside tpu-jupyter from the EEE mirror root (CPU only, cores 72-191). usage: eee_run.sh [NT=1] script args...
M=/home/yananlong/every_eval_ever/eci_work/v11/runs/EEE/_mirror/v11
exec sudo -n docker exec -u 2001:2001 -w $M -e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/tmp \
 -e OMP_NUM_THREADS=${NT:-1} -e OPENBLAS_NUM_THREADS=${NT:-1} -e MKL_NUM_THREADS=${NT:-1} -e NUMBA_NUM_THREADS=${NT:-1} \
 -e PYTHONPATH=/home/yananlong/every_eval_ever/eci_work/v11/runs/vendor/eci-public/src \
 tpu-jupyter taskset -c ${CORES:-72-191} /opt/venvs/jax/bin/python "$@"
