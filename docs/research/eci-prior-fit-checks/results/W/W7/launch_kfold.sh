#!/bin/bash
# W4 K-fold training fits of one W7 candidate, all five folds concurrently, 6-hour cap each.
# usage: launch_kfold.sh CAND FEATURES TARGET_ACCEPT   (status in runs/W/W7/logs/status.txt as "CAND_fold<k> exit ...")
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
C=$1; F=$2; TA=$3
for k in 0 1 2 3 4; do
  ( sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 21600 /opt/venvs/jax/bin/python runs/w7_fit.py --name $C --features $F --target-accept $TA --fold $k --seed $((12345+k)) > runs/W/W7/logs/${C}_fold$k.log 2>&1
    echo "${C}_fold$k exit $? $(date -u +%FT%TZ)" >> runs/W/W7/logs/status.txt ) &
  sleep 2
done
wait
