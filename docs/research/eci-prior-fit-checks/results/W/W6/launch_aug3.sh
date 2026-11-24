#!/bin/bash
# Cell model, fallback 1 (target acceptance 0.99), 6-hour cap.
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
for s in all ind; do
  ( sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 21600 /opt/venvs/jax/bin/python runs/aug_fit.py --set $s --model cell --target-accept 0.99 > runs/AUG/logs/AUG_cell_${s}_ta99.log 2>&1
    echo "AUG_cell_${s}_ta99 exit $? $(date -u +%FT%TZ)" >> runs/AUG/logs/status.txt ) &
done; wait
