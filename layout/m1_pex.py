#!/usr/bin/env python3
"""M1 post-layout extraction: flat R+C netlist of the submission GDS (gds/tt_um_chiranjitpatel_sar_adc.gds).

Runs Magic 8.3.623 from the LibreLane Docker image (the local Magic 8.3.411 runs extresist but its ext2spice
drops the resistors). Needs the Docker daemon (start it with: dockerd &).
  flatten -> extract -> extresist all (signal nets; VDPWR/VGND and the VGND-tied outputs are not
  resistance-extracted: their currents are uA, so IR drop is uV) -> ext2spice with R and C (cthresh 0.01 fF)
Output: sim/out/layout/m1_rc/m1_rc.spice, subckt renamed to tt_um_chiranjitpatel_sar_adc.
Also prints the effective resistance from each used pin to the devices it drives.
Usage: python3 layout/m1_pex.py [m2]   (output: sim/out/layout/<name>_rc/<name>_rc.spice)
m2: the LibreLane block adc_digital is not extracted (flat R+C of ~150 std cells made the whole-tile transient
~15x slower than the schematic). A copy of the GDS without the adc_digital instance is extracted, with a label
on each of its pins named after the top-level net (from layout/cells/m2_top_ref.spice), and the extracted
netlist gets an instance of LibreLane's adc_digital netlist (layout/digital/adc_digital.spice) on those nets.
The digital block's own timing is signed off by LibreLane's STA.
"""
import json, os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = "tt_um_chiranjitpatel_sar_adc"
NAME = sys.argv[1] if len(sys.argv) > 1 else "m1"
OUT = os.path.join(ROOT, "sim", "out", "layout", f"{NAME}_rc")
PDK = "/usr/local/share/pdk"
IMAGE = "ghcr.io/librelane/librelane:3.0.17"
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith((".ext", ".sim", ".nodes", ".spice")):
        os.remove(os.path.join(OUT, f))
ignore = ["VDPWR", "VGND"] + [f"{{{p}[{i}]}}" for p in ("uo_out", "uio_out", "uio_oe") for i in range(8)]
GDS = os.path.join(ROOT, "gds", f"{TOP}.gds")
XDIG = None
if NAME == "m2":
    import klayout.db as db
    sub = open(os.path.join(ROOT, "layout", "digital", "adc_digital.spice")).read().replace("\n+", " ")
    dports = re.search(r"^\.subckt adc_digital (.*)$", sub, re.M).group(1).split()
    ref = open(os.path.join(ROOT, "layout", "cells", "m2_top_ref.spice")).read().replace("\n+", " ")
    dnets = re.search(r"^xdig (.*) adc_digital$", ref, re.M).group(1).split()
    net_of = dict(zip(dports, dnets))
    XDIG = "Xdig " + " ".join(dnets) + " adc_digital"
    dig = json.load(open(os.path.join(ROOT, "sim", "out", "layout", "m2p", "pins.json")))["adc_digital"]
    bb = dig["bbox"]
    L = db.Layout(); L.read(GDS); top = L.cell(TOP)
    for inst in list(top.each_inst()):
        if inst.cell.name == "adc_digital":
            inst.delete()
    for port, pts in dig["pins"].items():
        net = net_of.get(port)
        if net is None or net in ("VDPWR", "VGND"):
            continue
        x, y, gl = pts[0]
        d = [x - bb[0], bb[2] - x, y - bb[1], bb[3] - y]
        k = d.index(min(d))                                  # patch of pin metal from the pin to its edge
        box = [(bb[0] - 0.05, y - 0.07, x + 0.07, y + 0.07), (x - 0.07, y - 0.07, bb[2] + 0.05, y + 0.07),
               (x - 0.07, bb[1] - 0.05, x + 0.07, y + 0.07), (x - 0.07, y - 0.07, x + 0.07, bb[3] + 0.05)][k]
        top.shapes(L.layer(gl, 20)).insert(db.DBox(*box))
        top.shapes(L.layer(gl, 5)).insert(db.DText(net, db.DTrans(x, y)))
    # the block's met4 power straps stay: the comparator and the inmux take VDPWR from straps 116.84 / 136.84,
    # which reach the VDPWR stripe only through the block's own power grid (its std-cell rails). That grid is
    # stood in for by a met3 bar across the VDPWR straps (via3 at each), inside the deleted block's area.
    m3, v3, m4 = L.layer(70, 20), L.layer(70, 44), L.layer(71, 20)
    ym = (bb[1] + bb[3]) / 2
    for net in ("VDPWR", "VGND"):
        xs = sorted({round(p[0], 3) for p in dig["pins"][net]})
        for x in xs:
            top.shapes(m4).insert(db.DBox(x - 0.6, bb[1], x + 0.6, bb[3]))
        if net == "VDPWR":
            top.shapes(m3).insert(db.DBox(xs[0] - 0.6, ym - 0.3, xs[-1] + 0.6, ym + 0.3))
            for x in xs:
                for dx in (-0.3, 0.1):
                    top.shapes(v3).insert(db.DBox(x + dx, ym - 0.1, x + dx + 0.2, ym + 0.1))
    GDS = os.path.join(OUT, f"{TOP}_nodig.gds")
    L.write(GDS)
tcl = f"""gds flatglob *__example_*
gds read {GDS}
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
if XDIG:
    # a net whose extracted part has a single device terminal (opb, onb: one comparator drain each) comes out
    # of extresist as <net>.t0 only, with no node at the label; the digital pin connects there
    body = txt.replace("\n+", " ")
    nets = XDIG.split()[1:-1]
    for k, n in enumerate(nets):
        if not re.search(rf"\s{re.escape(n)}(\s|$)", body, re.M) and re.search(rf"\s{re.escape(n)}\.t0\s", body):
            nets[k] = n + ".t0"
    XDIG = "Xdig " + " ".join(nets) + " adc_digital"
    i = txt.rindex(".ends")
    txt = (f".include {ROOT}/layout/digital/adc_digital.spice\n" + txt[:i] + XDIG + "\n" + txt[i:])
dst = os.path.join(OUT, f"{NAME}_rc.spice")
open(dst, "w").write(txt)
lines = txt.replace("\n+", " ").splitlines()
R = [l.split() for l in lines if l.startswith("R")]
C = [l for l in lines if l.startswith("C")]
summary = [f"{NAME}_rc.spice: {len(R)} R, {len(C)} C, " + re.search(r"Nets extracted: .*", r.stdout).group(0)]

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
for n in ("ua[0]", "ua[1]", "ui_in[3]", "ui_in[1]", "uio_in[3]"):
    v = reff(n)
    summary.append(f"R(pin {n} -> devices) = {v:.1f} Ohm" if v is not None else f"{n}: no R extracted")
print("\n".join(summary))
os.makedirs(os.path.join(ROOT, "sim", "out", NAME), exist_ok=True)
open(os.path.join(ROOT, "sim", "out", NAME, "extract.txt"), "w").write("\n".join(summary) + "\n")
