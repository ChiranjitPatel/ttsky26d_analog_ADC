#!/usr/bin/env bash
# Stage 4: netlist (incl. the bandgap loop-break copy via ../bandgap/run.sh's recipe), run, report.
set -euo pipefail
cd "$(dirname "$0")"
../../tools/netlist.sh bias_gen ota bandgap_core ptat_out > /dev/null
N=../out/netlist
sed -e 's/^\.subckt bandgap_core VDPWR VGND pbias pd vbg vgp$/.subckt bandgap_core VDPWR VGND pbias pd vbg vgp vo/' \
    -e 's/^xota VDPWR VGND pbias pd vb va vgp ota$/xota VDPWR VGND pbias pd vb va vo ota/' \
    $N/bandgap_core.spice > $N/bandgap_core_brk.spice
mkdir -p ../out/ptat
ngspice -b tb_ptat.spice > ../out/ptat/tb_ptat.log 2>&1 & p1=$!
ngspice -b tb_ptat_loop.spice > ../out/ptat/tb_ptat_loop.log 2>&1 & p2=$!
wait $p1; wait $p2
[ -f report.py ] && python3 report.py || true
