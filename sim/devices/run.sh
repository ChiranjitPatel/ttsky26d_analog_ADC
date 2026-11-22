#!/usr/bin/env bash
# Stage 0: run all device testbenches (in parallel; each takes ~40 s to load the models) and post-process.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../out/devices
pids=()
for t in mos pnp res mim; do
  ngspice -b "tb_$t.spice" > "../out/devices/tb_$t.log" 2>&1 & pids+=($!)
done
rc=0; for p in "${pids[@]}"; do wait "$p" || rc=1; done
[ $rc -eq 0 ] || { echo "a testbench failed, see ../out/devices/*.log"; exit 1; }
python3 stage0.py > /dev/null
echo "Stage 0 done: results.md, lut/, plots/"
