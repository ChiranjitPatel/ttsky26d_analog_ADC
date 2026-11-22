#!/usr/bin/env bash
# Long I2/I3 transistor-level runs (hours): I3 quick, I2 code edges, I2 64-point sine. Results in ../out/adc/.
cd "$(dirname "$0")"; export OMP_NUM_THREADS=1
for t in quick_ref edges sine64; do
  (ngspice -b tb_$t.spice > ../out/adc/tb_$t.log 2>&1; python3 decode.py $t > ../out/adc/$t.codes.txt 2>&1; echo "$t done $(date +%T)") &
done
wait
