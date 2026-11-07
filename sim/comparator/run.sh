#!/usr/bin/env bash
# Stage 6: netlist, run both comparator testbenches in parallel (slow: 5 ps timestep), report.
set -euo pipefail
cd "$(dirname "$0")"
../../tools/netlist.sh comparator > /dev/null
mkdir -p ../out/comparator
ngspice -b tb_cmp.spice > ../out/comparator/tb_cmp.log 2>&1 & p1=$!
ngspice -b tb_cmp_kick.spice > ../out/comparator/tb_cmp_kick.log 2>&1 & p2=$!
wait $p1; wait $p2
[ -f report.py ] && python3 report.py || true
