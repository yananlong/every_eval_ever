#!/bin/bash
# run a python script in the tpu-jupyter container, CPU only, cores 72-191, 1 thread
exec sudo -n docker exec -u 2001:2001 -w /home/yananlong/every_eval_ever/eci_work/v11 -e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/tmp \
 -e OMP_NUM_THREADS=${NT:-1} -e OPENBLAS_NUM_THREADS=${NT:-1} -e MKL_NUM_THREADS=${NT:-1} -e NUMBA_NUM_THREADS=${NT:-1} \
 -e PYTHONPATH=/home/yananlong/every_eval_ever/eci_work/v11/runs/vendor/eci-public/src:/home/yananlong/every_eval_ever/eci_work/v11/runs:/home/yananlong/every_eval_ever/eci_work/tools ${EXTRA_ENV} \
 tpu-jupyter taskset -c 72-191 /opt/venvs/jax/bin/python "$@"
