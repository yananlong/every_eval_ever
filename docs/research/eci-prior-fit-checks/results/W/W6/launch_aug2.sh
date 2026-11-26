#!/bin/bash
# Cell-model pilot diagnostics and the cell-mean fits, in parallel.
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
R="sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 10800 /opt/venvs/jax/bin/python"
for s in all ind; do
  ( $R runs/aug_fit.py --set $s --model mean > runs/AUG/logs/AUG_mean_$s.log 2>&1; echo "AUG_mean_$s exit $? $(date -u +%FT%TZ)" >> runs/AUG/logs/status.txt ) &
  ( $R runs/aug_pilot_diag.py $s > runs/AUG/logs/pilot_diag_$s.log 2>&1; echo "pilot_diag_$s exit $? $(date -u +%FT%TZ)" >> runs/AUG/logs/status.txt ) &
done; wait
