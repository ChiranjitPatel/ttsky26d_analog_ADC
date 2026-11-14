#!/usr/bin/env bash
# M1 post-layout: extract (layout/m1_pex.py, needs Docker), write the testbenches, run schematic vs layout, report.
set -euo pipefail
cd "$(dirname "$0")"
[ "${1:-}" = "--no-extract" ] || python3 ../../layout/m1_pex.py
python3 make_tb.py > /dev/null
mkdir -p ../out/m1
pids=()
for d in sch rc; do for t in op ac tran; do ngspice -b tb_m1_${d}_$t.spice > ../out/m1/${d}_$t.log 2>&1 & pids+=($!); done; done
for p in "${pids[@]}"; do wait $p; done
[ -f report.py ] && python3 report.py || true
