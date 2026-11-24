#!/bin/bash
# K-fold training fits for registered candidates (same args/seeds as w6_expand), concurrently. usage: launch_kfold.sh NAME:FEATURE ...
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
PY=/opt/venvs/jax/bin/python
for nf in "$@"; do n=${nf%%:*}; feat=${nf#*:}
  for f in 0 1 2 3 4; do
    ( sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 $PY runs/w6_fit_one.py --name $n --features $feat --prior epoch --fold $f --seed $((12345+f)) > runs/W/W6/logs/kfold_${n}_$f.log 2>&1
      echo "kfold $n $f exit $? $(date -u +%FT%TZ)" >> runs/W/W6/logs/par_status.txt ) &
    sleep 3
  done
done
wait; echo KFOLD_DONE "$@" >> runs/W/W6/logs/par_status.txt
