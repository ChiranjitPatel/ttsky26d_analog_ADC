#!/usr/bin/env python3
"""M1 post-layout extraction: flat R+C netlist of the submission GDS (gds/tt_um_chiranjitpatel_sar_adc.gds).

Runs Magic 8.3.623 from the LibreLane Docker image (the local Magic 8.3.411 runs extresist but its ext2spice
drops the resistors). Needs the Docker daemon (start it with: dockerd &).
  flatten -> extract -> extresist all (signal nets; VDPWR/VGND and the VGND-tied outputs are not
  resistance-extracted: their currents are uA, so IR drop is uV) -> ext2spice with R and C (cthresh 0.01 fF)
Output: sim/out/layout/m1_rc/m1_rc.spice, subckt renamed to tt_um_chiranjitpatel_sar_adc.
Also prints the effective resistance from each used pin to the devices it drives.
Usage: python3 layout/m1_pex.py
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = "tt_um_chiranjitpatel_sar_adc"
OUT = os.path.join(ROOT, "sim", "out", "layout", "m1_rc")
PDK = "/usr/local/share/pdk"
IMAGE = "ghcr.io/librelane/librelane:3.0.17"
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith((".ext", ".sim", ".nodes", ".spice")):
        os.remove(os.path.join(OUT, f))
ignore = ["VDPWR", "VGND"] + [f"{{{p}[{i}]}}" for p in ("uo_out", "uio_out", "uio_oe") for i in range(8)]
tcl = f"""gds flatglob *__example_*
gds read {ROOT}/gds/{TOP}.gds
load {TOP}
flatten tt_flat
load tt_flat
select top cell
cd {OUT}
extract do local
extract all
ext2sim labels on
ext2sim
extresist tolerance 0.001
""" + "".join(f"extresist ignore {n}\n" for n in ignore) + """extresist all
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
src = os.path.join(OUT, "tt_flat.spice")
if not os.path.exists(src):
    sys.exit(f"extraction failed, see {OUT}/magic.log")
txt = open(src).read().replace(".subckt tt_flat ", f".subckt {TOP} ")
dst = os.path.join(OUT, "m1_rc.spice")
open(dst, "w").write(txt)
lines = txt.replace("\n+", " ").splitlines()
R = [l.split() for l in lines if l.startswith("R")]
C = [l for l in lines if l.startswith("C")]
summary = [f"m1_rc.spice: {len(R)} R, {len(C)} C, " + re.search(r"Nets extracted: .*", r.stdout).group(0)]

# effective resistance from a pin to the device terminals on its net (all terminals tied together)
dev = set()
for l in lines:
    if l.startswith("X"):
        for x in l.split()[1:]:
            if "=" in x or x.startswith("sky130"):
                break
            dev.add(x)
def reff(net):
    rs = [x for x in R if x[1] == net or x[1].startswith(net + ".n")]
    nodes = sorted({n for x in rs for n in x[1:3]})
    if net not in nodes:
        return None
    idx = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for x in rs:
        a, b, g = idx[x[1]], idx[x[2]], 1 / float(x[3])
        G[a, a] += g; G[b, b] += g; G[a, b] -= g; G[b, a] -= g
    keep = [i for i, n in enumerate(nodes) if not (n in dev and n != net)]
    I = np.zeros(len(keep)); I[keep.index(idx[net])] = 1
    return np.linalg.solve(G[np.ix_(keep, keep)], I)[keep.index(idx[net])]
for n in ("ua[1]", "ui_in[3]", "ui_in[1]", "uio_in[3]"):
    v = reff(n)
    summary.append(f"R(pin {n} -> devices) = {v:.1f} Ohm" if v is not None else f"{n}: no R extracted")
print("\n".join(summary))
os.makedirs(os.path.join(ROOT, "sim", "out", "m1"), exist_ok=True)
open(os.path.join(ROOT, "sim", "out", "m1", "extract.txt"), "w").write("\n".join(summary) + "\n")
