#!/bin/bash
# Exploratory family candidates (runs/w6x_family.py), real-data fits, concurrently; W5 environment.
cd /home/yananlong/every_eval_ever/eci_work/v11; mkdir -p runs/W/W6X/logs
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
PY=/opt/venvs/jax/bin/python
run() { name=$1; shift
  sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 10800 $PY runs/w6x_fit_family.py --name $name "$@" > runs/W/W6X/logs/$name.log 2>&1
  echo "$name exit $? $(date -u +%FT%TZ)" >> runs/W/W6X/logs/status.txt; }
echo "launch $(date -u +%FT%TZ)" >> runs/W/W6X/logs/status.txt
run FX_lin --variant lin & sleep 3
run FX_tag --variant tag & sleep 3
run FX_both --variant both & sleep 3
run FX_both_dev --variant both --features dev &
wait; echo ALL_DONE >> runs/W/W6X/logs/status.txt
