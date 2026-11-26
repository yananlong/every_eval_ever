#!/usr/bin/env bash
# Runs inside tpu-jupyter: PROV refits, PROV_P concurrent (default 44; 4 chains each = 176 cores on 0-191), 1 thread/proc, 2 h cap per attempt.
# usage: run_prov.sh ID...   Finished fits (status json with finished=true) are skipped by prov_run_entry.py (resumable).
cd /home/yananlong/every_eval_ever/eci_work/v11; mkdir -p runs/logs runs/EEE/PROV
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/tmp
export PYTHONPATH=$PWD/runs/vendor/eci-public/src:$PWD/runs:$PWD/../tools
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "=== launch $(date -u +%FT%TZ) n=$# ids=$*" >> runs/logs/prov_launch.log
printf '%s\n' "$@" | xargs -P ${PROV_P:-44} -I{} sh -c 'sleep $((RANDOM % 20)); taskset -c 0-191 /opt/venvs/jax/bin/python -W ignore ../tools/prov_run_entry.py {} >> runs/logs/prov_{}.log 2>&1; echo "$(date -u +%FT%TZ) finished {} rc=$?" >> runs/logs/prov_launch.log'
echo "=== all done $(date -u +%FT%TZ)" >> runs/logs/prov_launch.log
