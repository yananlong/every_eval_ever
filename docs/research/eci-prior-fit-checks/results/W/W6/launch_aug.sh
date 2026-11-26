#!/bin/bash
# Augmented-input fits in parallel. usage: launch_aug.sh
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
for s in all ind; do for m in base cell; do
  ( sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 10800 /opt/venvs/jax/bin/python runs/aug_fit.py --set $s --model $m > runs/AUG/logs/AUG_${m}_$s.log 2>&1
    echo "AUG_${m}_$s exit $? $(date -u +%FT%TZ)" >> runs/AUG/logs/status.txt ) &
done; done; wait
