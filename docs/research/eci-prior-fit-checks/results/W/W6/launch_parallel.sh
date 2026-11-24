#!/bin/bash
# W6 candidates F1-F5 fitted concurrently (deviation from the serial run order; per-fit args and caps as in w6_expand.fit_candidate).
# Environment mirrors tools/run_w5.sh: CPU only, 1 thread per process, cores 0-191.
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
PY=/opt/venvs/jax/bin/python
run() { name=$1; shift
  sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 "$@" > runs/W/W6/logs/par_$name.log 2>&1
  echo "$name exit $? $(date -u +%FT%TZ)" >> runs/W/W6/logs/par_status.txt; }
echo "launch $(date -u +%FT%TZ)" >> runs/W/W6/logs/par_status.txt
run F1 timeout 3600 $PY runs/w6_fit_one.py --name F1 --features 2d --prior epoch --cap4000 & sleep 3
run F2 $PY runs/w6_fit_one.py --name F2 --features dev --prior epoch & sleep 3
run F3 $PY runs/w6_fit_one.py --name F3 --features asym --prior epoch & sleep 3
run F4 $PY runs/w6_fit_one.py --name F4 --features drift --prior epoch & sleep 3
run F5 $PY runs/w6_fit_one.py --name F5 --features hetero --prior epoch &
wait; echo ALL_DONE >> runs/W/W6/logs/par_status.txt
