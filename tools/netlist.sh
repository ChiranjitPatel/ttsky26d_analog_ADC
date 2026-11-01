#!/usr/bin/env bash
# Netlist an xschem cell as a .subckt for ngspice testbenches.
#   tools/netlist.sh bias_gen      ->  sim/out/netlist/bias_gen.spice
set -euo pipefail
cd "$(dirname "$0")/../xschem"
export PDK_ROOT=${PDK_ROOT:-/usr/local/share/pdk}
out=../sim/out/netlist
mkdir -p "$out"
for cell in "$@"; do
  timeout 120 xschem --rcfile xschemrc --no_x -q -n -s -o "$out" "$cell.sch" > "$out/$cell.xschem.log" 2>&1
  f="$out/$cell.spice"
  if grep -q "IS MISSING" "$f"; then echo "netlist $cell: missing symbols"; grep "IS MISSING" "$f"; exit 1; fi
  # xschem writes the top cell's .subckt/.ends commented out; enable them
  sed -i -e 's/^\*\*\.subckt /.subckt /' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "$f"
  echo "netlist: $f"
done
