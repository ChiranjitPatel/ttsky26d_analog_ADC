#!/usr/bin/env bash
# Stage 3: netlist, make the loop-break copy, run both testbenches in parallel, report.
set -euo pipefail
cd "$(dirname "$0")"
../../tools/netlist.sh bias_gen ota bandgap_core > /dev/null
N=../out/netlist
# loop-break copy: OTA output becomes a separate port 'vo'
sed -e 's/^\.subckt bandgap_core VDPWR VGND pbias pd vbg vgp$/.subckt bandgap_core VDPWR VGND pbias pd vbg vgp vo/' \
    -e 's/^xota VDPWR VGND pbias pd vb va vgp ota$/xota VDPWR VGND pbias pd vb va vo ota/' \
    $N/bandgap_core.spice > $N/bandgap_core_brk.spice
grep -q "^xota .* vo ota$" $N/bandgap_core_brk.spice || { echo "loop-break edit failed"; exit 1; }
mkdir -p ../out/bandgap
ngspice -b tb_bandgap.spice > ../out/bandgap/tb_bandgap.log 2>&1 & p1=$!
ngspice -b tb_bandgap_loop.spice > ../out/bandgap/tb_bandgap_loop.log 2>&1 & p2=$!
ngspice -b tb_bandgap_pd.spice > ../out/bandgap/tb_bandgap_pd.log 2>&1 & p3=$!
wait $p1; wait $p2; wait $p3
[ -f report.py ] && python3 report.py || true
