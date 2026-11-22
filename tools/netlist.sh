#!/usr/bin/env bash
# Netlist an xschem cell as a .subckt for ngspice testbenches.
#   tools/netlist.sh bias_gen      ->  sim/out/netlist/bias_gen.spice
set -euo pipefail
cd "$(dirname "$0")/../xschem"
export PDK_ROOT=${PDK_ROOT:-/usr/local/share/pdk}
out=../sim/out/netlist
mkdir -p "$out"
# Regenerate every schematic from its generator first, so a .sch can never drift from gen_*.py
# (stage 3's parameter sweep once left a stale bandgap_core.sch behind; see sim/bandgap/README.md).
# Leaf cells first: hierarchical generators read the symbols of the cells they instantiate.
order="bias_gen ota bandgap_core ptat_out vref_filt vref_buf vref_sel comparator inmux vcm_gen dac adc_core top"
gens=""; for c in $order; do gens="$gens gen_$c.py"; done
for g in gen_*.py; do case " $gens " in *" $g "*) ;; *) gens="$gens $g";; esac; done
for g in $gens; do python3 "$g" > /dev/null || { echo "generator $g failed"; exit 1; }; done
rm -rf ../tools/__pycache__
for cell in "$@"; do
  timeout 120 xschem --rcfile xschemrc --no_x -q -n -s -o "$out" "$cell.sch" > "$out/$cell.xschem.log" 2>&1
  f="$out/$cell.spice"
  if grep -q "IS MISSING" "$f"; then echo "netlist $cell: missing symbols"; grep "IS MISSING" "$f"; exit 1; fi
  # xschem writes the top cell's .subckt/.ends commented out; enable them
  # (long port lists continue on '*+' lines, which must be enabled too)
  awk 'BEGIN{h=0} /^\*\*\.subckt /{sub(/^\*\*/,""); h=1; print; next}
       h && /^\*\+/{sub(/^\*/,""); print; next} {h=0} /^\*\*\.ends/{sub(/^\*\*/,"")} !/^\.end$/{print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  echo "netlist: $f"
done
