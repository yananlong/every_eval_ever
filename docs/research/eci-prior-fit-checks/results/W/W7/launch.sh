#!/bin/bash
# One W7 fit, 6-hour cap. usage: launch.sh NAME ARGS...   (status in runs/W/W7/logs/status.txt)
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
name=$1; shift
sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 21600 /opt/venvs/jax/bin/python runs/w7_fit.py --name $name "$@" > runs/W/W7/logs/$name.log 2>&1
echo "$name exit $? $(date -u +%FT%TZ)" >> runs/W/W7/logs/status.txt
