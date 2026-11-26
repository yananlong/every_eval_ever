#!/usr/bin/env bash
# Runs inside tpu-jupyter: BSEL refits, at most 16 concurrent (4 chains each = 64 chain processes on cores 0-63), 1 thread/proc,
# 2 h cap per attempt (inside bsel_run_entry.py).  usage: run_bsel.sh ID...   (queue order = argument order)
cd /home/yananlong/every_eval_ever/eci_work/v11; mkdir -p runs/logs
export JAX_PLATFORMS=cpu TPU_VISIBLE_CHIPS= HOME=/tmp
export PYTHONPATH=$PWD/runs/vendor/eci-public/src
export BSEL_SEED
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "=== launch $(date -u +%FT%TZ) n=$# ids=$*" >> runs/logs/bsel_launch.log
rm -f /tmp/bsel_slot_*
printf '%s\n' "$@" | xargs -P ${BSEL_P:-16} --process-slot-var=SLOT -I{} sh -c '[ -e /tmp/bsel_slot_$SLOT ] || { touch /tmp/bsel_slot_$SLOT; sleep $((SLOT * 4)); }; taskset -c 0-63 /opt/venvs/jax/bin/python -W ignore ../tools/bsel_run_entry.py {} --seed ${BSEL_SEED:-12345} > runs/logs/bsel_{}${BSEL_SEED:+__s$BSEL_SEED}.log 2>&1; echo "$(date -u +%FT%TZ) finished {} rc=$?" >> runs/logs/bsel_launch.log'
echo "=== all done $(date -u +%FT%TZ)" >> runs/logs/bsel_launch.log
