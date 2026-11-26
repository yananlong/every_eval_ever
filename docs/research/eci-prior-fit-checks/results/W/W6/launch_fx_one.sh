#!/bin/bash
# One exploratory family fit. usage: launch_fx_one.sh NAME ARGS...
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
name=$1; shift
sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 10800 /opt/venvs/jax/bin/python runs/w6x_fit_family.py --name $name "$@" > runs/W/W6X/logs/$name.log 2>&1
echo "$name exit $? $(date -u +%FT%TZ)" >> runs/W/W6X/logs/status.txt
