#!/usr/bin/env bash
# Stage 5: netlist, run the three testbenches in parallel, report.
set -euo pipefail
cd "$(dirname "$0")"
../../tools/netlist.sh bias_gen ota bandgap_core vref_filt vref_buf vref_sel > /dev/null
mkdir -p ../out/vref
pids=()
for t in tb_vref tb_vref_buf tb_vref_sel; do ngspice -b $t.spice > ../out/vref/$t.log 2>&1 & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
[ -f report.py ] && python3 report.py || true
