#!/usr/bin/env python3
"""Block-level layout checks: Magic DRC, Magic extraction from GDS, netgen LVS against the xschem netlist.

Usage (from anywhere):
    python3 layout/check_cell.py bias_gen                       # layout/cells/bias_gen.gds
    python3 layout/check_cell.py bias_gen --gds path/to/x.gds   # another GDS (e.g. straight from KLayout)
    python3 layout/check_cell.py bias_gen --pex                 # also write an RC-extracted netlist
Inputs:
    GDS with a top cell named like the block (default layout/cells/<cell>.gds)
    schematic netlist sim/out/netlist/<cell>.spice (tools/netlist.sh <cell>)
Outputs (all in sim/out/layout/<cell>/, ignored by git):
    drc.txt      Magic DRC errors (count + where)
    <cell>.ext.spice   extracted netlist for LVS (no parasitics)
    <cell>.pex.spice   with --pex: R+C extracted netlist for post-layout simulation
    lvs.txt      netgen report
Exit code 0 only if DRC is clean and the netlists match.
This is the same flow as the TRNG project: GDS -> Magic -> extract -> netgen.
"""
import argparse, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDK = os.environ.get("PDK_ROOT", "/usr/local/share/pdk")
TECH = os.path.join(PDK, "sky130A", "libs.tech")

ap = argparse.ArgumentParser()
ap.add_argument("cell")
ap.add_argument("--gds")
ap.add_argument("--netlist")
ap.add_argument("--pex", action="store_true")
a = ap.parse_args()
cell = a.cell
gds = os.path.abspath(a.gds or os.path.join(ROOT, "layout", "cells", f"{cell}.gds"))
sch = os.path.abspath(a.netlist or os.path.join(ROOT, "sim", "out", "netlist", f"{cell}.spice"))
out = os.path.join(ROOT, "sim", "out", "layout", cell)
os.makedirs(out, exist_ok=True)
for f in (gds, sch):
    if not os.path.exists(f):
        sys.exit(f"missing {f}")

pex = ""
if a.pex:
    pex = f"""
extract all
ext2sim labels on
ext2sim
extresist tolerance 10
extresist all
ext2spice lvs
ext2spice cthresh 0.01
ext2spice extresist on
ext2spice -o {out}/{cell}.pex.spice
"""
tcl = f"""
drc off
gds flatglob *__example_*
gds read {gds}
load {cell}
select top cell
# grow the box: Magic marks an error as the region where the rule fails, which can lie outside
# the cell's bounding box, and 'drc listall' only returns errors inside the box
box grow c 5um
drc on
drc style drc(full)
drc check
drc catchup
# count from the full error list ('drc list count total' gave 0 while 'drc listall why' listed errors)
set why [drc listall why]
set n 0
foreach {{rule boxes}} $why {{ incr n [llength $boxes] }}
set fp [open {out}/drc.txt w]
puts $fp "DRC_COUNT $n"
foreach {{rule boxes}} $why {{
    puts $fp "$rule: [llength $boxes]"
    foreach b [lrange $boxes 0 199] {{ puts $fp "    $b" }}
}}
close $fp
puts "DRC_COUNT $n"
cd {out}
extract do local
extract all
ext2spice lvs
ext2spice -o {out}/{cell}.ext.spice
{pex}
quit -noprompt
"""
tclf = os.path.join(out, "magic.tcl")
open(tclf, "w").write(tcl)
rc = os.path.join(TECH, "magic", "sky130A.magicrc")
r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", rc, tclf], capture_output=True, text=True, cwd=out)
open(os.path.join(out, "magic.log"), "w").write(r.stdout + r.stderr)
m = re.search(r"DRC_COUNT (\d+)", r.stdout)
drc = int(m.group(1)) if m else -1
print(f"Magic DRC: {drc} errors" + ("" if drc == 0 else f"  (see {out}/drc.txt)"))
ext = os.path.join(out, f"{cell}.ext.spice")
if not os.path.exists(ext):
    sys.exit(f"extraction failed, see {out}/magic.log")

# netgen LVS: layout first, schematic second
rep = os.path.join(out, "lvs.txt")
setup = os.path.join(TECH, "netgen", "sky130A_setup.tcl")
r = subprocess.run(["netgen", "-batch", "lvs", f"{ext} {cell}", f"{sch} {cell}", setup, rep],
                   capture_output=True, text=True, cwd=out)
open(os.path.join(out, "netgen.log"), "w").write(r.stdout + r.stderr)
txt = open(rep).read() if os.path.exists(rep) else ""
topo = "Circuits match uniquely" in txt or "Netlists match uniquely" in txt
props = "Property errors were found" in txt or "with property errors" in txt
ok = topo and not props
print("LVS: " + ("match" if ok else
                 f"device sizes differ (property errors)  (see {rep})" if topo else f"MISMATCH  (see {rep})"))
for line in txt.splitlines():
    if re.search(r"Number of (devices|nets)|Final result|do not match|Property errors|property errors:|  \S+ +\S+ +\S+ +\(", line):
        print("   ", line.strip())
if a.pex:
    print(f"post-layout netlist: {out}/{cell}.pex.spice")
sys.exit(0 if drc == 0 and ok else 1)
