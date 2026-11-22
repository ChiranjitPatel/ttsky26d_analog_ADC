#!/usr/bin/env python3
"""Post-layout R+C extraction of one cell (layout/cells/<cell>.gds), same Magic flow as layout/m1_pex.py.

Output: sim/out/layout/<cell>_rc/<cell>_rc.spice with
  .subckt <cell>_x <extracted port order>   (Magic's netlist)
  .subckt <cell>_pl <schematic port order>  (wrapper; port order from layout/cells/m2_top_ref.spice)
so a testbench swaps `comparator` for `comparator_pl` without touching its instance lines.
VDPWR/VGND are not resistance-extracted (as in m1_pex.py). Needs the Docker daemon (dockerd &).
Usage: python3 layout/cell_pex.py comparator
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL = sys.argv[1]
OUT = os.path.join(ROOT, "sim", "out", "layout", f"{CELL}_rc")
PDK = "/usr/local/share/pdk"
IMAGE = "ghcr.io/librelane/librelane:3.0.17"
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith((".ext", ".sim", ".nodes", ".spice")):
        os.remove(os.path.join(OUT, f))
GDS = os.path.join(ROOT, "layout", "cells", f"{CELL}.gds")
tcl = f"""gds flatglob *__example_*
gds read {GDS}
load {CELL}
flatten {CELL}_x
load {CELL}_x
select top cell
cd {OUT}
extract do local
extract all
ext2sim labels on
ext2sim
extresist tolerance 0.001
extresist ignore VDPWR
extresist ignore VGND
extresist all
ext2spice hierarchy off
ext2spice format ngspice
ext2spice subcircuit top on
ext2spice cthresh 0.01
ext2spice rthresh 0
ext2spice extresist on
ext2spice
quit -noprompt
"""
open(os.path.join(OUT, "rc.tcl"), "w").write(tcl)
r = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-v", f"{PDK}:{PDK}", "-w", OUT, IMAGE,
                    "magic", "-dnull", "-noconsole", "-rcfile", f"{PDK}/sky130A/libs.tech/magic/sky130A.magicrc", "rc.tcl"],
                   capture_output=True, text=True)
open(os.path.join(OUT, "magic.log"), "w").write(r.stdout + r.stderr)
src = os.path.join(OUT, f"{CELL}_x.spice")
if not os.path.exists(src):
    sys.exit(f"extraction failed, see {OUT}/magic.log")
txt = open(src).read()
body = txt.replace("\n+", " ")
xports = re.search(rf"^\.subckt {CELL}_x (.*)$", body, re.M).group(1).split()
ref = open(os.path.join(ROOT, "layout", "cells", "m2_top_ref.spice")).read().replace("\n+", " ")
sports = re.search(rf"^\.subckt {CELL} (.*)$", ref, re.M).group(1).split()
nodes = set(body.split())
conn = []
for p in xports:                       # a port that extresist renamed keeps its label name in the wrapper
    conn.append(re.sub(r"\.t\d+$", "", p))
missing = [p for p in sports if p not in conn]
if missing:
    sys.exit(f"ports missing from the extracted netlist: {missing}")
txt += f"\n.subckt {CELL}_pl {' '.join(sports)}\nX1 {' '.join(conn)} {CELL}_x\n.ends\n"
dst = os.path.join(OUT, f"{CELL}_rc.spice")
open(dst, "w").write(txt)
lines = body.splitlines()
print(f"{dst}: {sum(l.startswith('R') for l in lines)} R, {sum(l.startswith('C') for l in lines)} C; "
      f"ports {xports}")
