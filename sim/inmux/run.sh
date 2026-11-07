#!/usr/bin/env bash
# Stage 7: netlist, run both testbenches in parallel, report.
set -euo pipefail
cd "$(dirname "$0")"
../../tools/netlist.sh bias_gen ota bandgap_core ptat_out inmux vcm_gen > /dev/null
mkdir -p ../out/inmux
ngspice -b tb_inmux.spice > ../out/inmux/tb_inmux.log 2>&1 & p1=$!
ngspice -b tb_sample.spice > ../out/inmux/tb_sample.log 2>&1 & p2=$!
wait $p1; wait $p2
[ -f report.py ] && python3 report.py || true
