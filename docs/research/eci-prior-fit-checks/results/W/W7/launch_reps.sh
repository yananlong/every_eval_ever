#!/bin/bash
# Model-true replicates of one W7 candidate. usage: launch_reps.sh CAND FEATURES TARGET_ACCEPT R PARALLEL [SRC_NC|-] [FIRST LAST]
cd /home/yananlong/every_eval_ever/eci_work/v11
E="-e JAX_PLATFORMS=cpu -e TPU_VISIBLE_CHIPS= -e HOME=/home/yananlong/every_eval_ever/eci_work/home -e PYTHONPATH=$PWD/runs/vendor/eci-public/src -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1"
C=$1; F=$2; TA=$3; R=$4; P=$5; S6=${6:--}; SRC=$([ "$S6" != "-" ] && echo "--src $S6"); FIRST=${7:-0}; LAST=${8:-$((R-1))}; mkdir -p runs/W/W7/rep/$C/logs
seq $FIRST $LAST | xargs -P $P -I{} sh -c "sudo -n docker exec -u 2001:2001 -w $PWD $E tpu-jupyter taskset -c 0-191 timeout 21600 /opt/venvs/jax/bin/python runs/w7_rep.py --cand $C --features $F --r {} --R $R --target-accept $TA $SRC > runs/W/W7/rep/$C/logs/r{}.log 2>&1; echo \"r{} exit \$? \$(date -u +%FT%TZ)\" >> runs/W/W7/rep/$C/logs/status.txt"
