#!/bin/bash
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 3600 /opt/venvs/jax/bin/python runs/w6_fit_one.py --name F1_ta99 --features 2d --prior epoch --cap4000 --target-accept 0.99 > runs/W/W6/logs/par_F1_ta99.log 2>&1
rc=$?; echo "F1_ta99 exit $rc $(date -u +%FT%TZ)" >> runs/W/W6/logs/par_status.txt; [ $rc = 124 ] && date -u +%FT%TZ > runs/W/W6/F1_ta99.timeout; exit 0
