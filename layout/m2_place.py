#!/usr/bin/env python3
"""M2 — full ADC chip: top-level integration of all cells on floorplan v4 (Magic). PHASE 1 (placement only).

Builds tt_um_chiranjitpatel_sar_adc with
  * the M0 frame: outline + pins from tt_analog_1x2.def, VDPWR/VGND met4 stripes (floorplan_v3.json,
    y = 1 ... 217), the 24 outputs tied to VGND (met3 bar at y = 219.5), met4 stubs on ua[0]/ua[1];
  * the M1 cells (layout/cells/*.gds) at their floorplan-v3 positions (vref_filt rotated 180 degrees);
  * the wiring between them, in the reserved corridors (G1/G2/G3 between left-column blocks, R1/R2
    vertical, B1 along the bottom, T1 along the top), crossing the power stripes on met3;
  * power: every block's rails to its nearest stripes (met1 + via stacks), and internal ties joining all
    stripes of a net: met3 straps along the bottom (VDPWR y = 1.3, VGND y = 6.7) with via3 up into each stripe.
M1 has no digital block: BG_PD = ui_in[3], VREF_OE = ui_in[1], REF_SEL = uio_in[3] are wired straight in.
Outputs: build to sim/out/layout/m1 (mag, gds, lef) and the LVS reference layout/cells/m1_top_ref.spice.
  python3 layout/m1_top.py            build + Magic DRC count
  python3 layout/m1_top.py --install  also copy gds/lef/mag over the submission files (gds/, lef/, mag/)
"""
import json, os, re, shutil, subprocess, sys
import klayout.db as db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import RC, f

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = "tt_um_chiranjitpatel_sar_adc"
DEF = os.path.join(ROOT, "layout", "tt_analog_1x2.def")
OUT = os.path.join(ROOT, "sim", "out", "layout", "m2p")
FP = json.load(open(os.path.join(ROOT, "layout", "floorplan_v4.json")))
CELLS = ["bias_gen", "bandgap_core", "vref_filt", "ptat_out", "vref_sel", "vref_buf",
         "inmux", "vcm_gen", "dac", "comparator", "adc_digital"]
os.makedirs(OUT, exist_ok=True)
for fn in os.listdir(OUT):                 # stale .mag files in Magic's working directory would be loaded
    if fn.endswith(".mag") or fn.endswith(".ext"):  # instead of the fresh cells (2026-11-14: hung at a prompt)
        os.remove(os.path.join(OUT, fn))

T = ["drc off", "snap internal"]
def paint(layer, x0, y0, x1, y1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    T.extend([f"box {f(x0)} {f(y0)} {f(x1)} {f(y1)}", f"paint {layer}"])
def hwire(layer, x0, x1, y, w):
    paint(layer, min(x0, x1) - w / 2, y - w / 2, max(x0, x1) + w / 2, y + w / 2)
def vwire(layer, x, y0, y1, w):
    paint(layer, x - w / 2, min(y0, y1) - w / 2, x + w / 2, max(y0, y1) + w / 2)
LAYERS = ["metal1", "metal2", "metal3", "metal4"]
CUTS = {("metal1", "metal2"): ("via1", 0.26, 0.44), ("metal2", "metal3"): ("via2", 0.32, 0.5),
        ("metal3", "metal4"): ("via3", 0.4, 0.6)}
def stack(x, y, lo, hi):
    """Via stack from layer lo to layer hi at (x, y), with landing pads (via2 >= 0.32: Magic drops smaller)."""
    i0, i1 = LAYERS.index(lo), LAYERS.index(hi)
    for i in range(i0, i1):
        cut, s, pad = CUTS[(LAYERS[i], LAYERS[i + 1])]
        paint(LAYERS[i], x - pad / 2, y - pad / 2, x + pad / 2, y + pad / 2)
        paint(LAYERS[i + 1], x - pad / 2, y - pad / 2, x + pad / 2, y + pad / 2)
        paint(cut, x - s / 2, y - s / 2, x + s / 2, y + s / 2)

# ---------------------------------------------------------------- block cells first, then the frame
# (a 'gds read' after the top cell exists left Magic editing the wrong cell - 2026-11-14)
T += [f"gds read {os.path.join(ROOT, 'layout', 'cells', c + '.gds')}" for c in CELLS]
# a fresh, empty cell must be current before 'def read' (otherwise the frame lands in the last block read)
T += ["load m2_scratch", "edit", f"def read {DEF}", f"cellname rename tt_um_template {TOP}", f"load {TOP}", "edit"]
SY0, SY1 = FP["stripe_y"]
for net, x0, x1 in FP["stripes"]:
    T += [f"box {f(x0)} {f(SY0)} {f(x1)} {f(SY1)}", "paint met4", f"label {net} FreeSans 0.25u -met4", "port make",
          f"port use {'ground' if net == 'VGND' else 'power'}", "port class bidirectional", "port connections n s e w"]
d = open(DEF).read()
pins = {n: (int(x) / 1000, int(y) / 1000) for n, x, y in re.findall(r"- (\S+) \+ NET .*?\+ PLACED \( (\d+) (\d+) \) N ;", d, re.S)}
outs = sorted([(n, x) for n, (x, y) in pins.items() if re.match(r"u(o_out|io_out|io_oe)\[", n)], key=lambda t: t[1])
TIE = 219.5
vg0 = min(x0 for n, x0, x1 in FP["stripes"] if n == "VGND")
paint("metal3", vg0, TIE - 0.3, outs[-1][1] + 0.3, TIE + 0.3)
stack(vg0 + 1.0, TIE, "metal3", "metal4")
paint("metal4", vg0, SY1 - 1, vg0 + 2.0, TIE + 0.5)                       # left VGND stripe up to the bar
for n, x in outs:
    ytop = pins[n][1] - 0.5
    paint("metal4", x - 0.15, TIE - 0.3, x + 0.15, ytop)
    paint("via3", x - 0.2, TIE - 0.25, x + 0.2, TIE + 0.25)
    paint("metal4", x - 0.3, TIE - 0.35, x + 0.3, TIE + 0.35)
for n in ("ua[0]", "ua[1]"):                                               # stubs (ua[1] continues to the pad route)
    x = pins[n][0]
    paint("metal4", x - 0.45, 0.0, x + 0.45, 5.4 if n == "ua[1]" else 4.0)

# ---------------------------------------------------------------- blocks
def gds_info(c):
    l = db.Layout(); l.read(os.path.join(ROOT, "layout", "cells", f"{c}.gds")); t = l.top_cell(); b = t.bbox()
    labs = {}
    for li in l.layer_indexes():
        for s in t.shapes(li).each():
            if s.is_text():
                labs[s.text.string] = (s.text.x * l.dbu, s.text.y * l.dbu)
    return (b.left * l.dbu, b.bottom * l.dbu, b.right * l.dbu, b.top * l.dbu), labs
P = {}            # absolute pin positions per block
for c in CELLS:
    bb, labs = gds_info(c)
    rect = FP["blocks"][c]["rect"]; orient = FP["blocks"][c]["orient"]
    x0, y0 = rect[0], rect[1]
    if orient == "R180":
        tr = lambda x, y, bb=bb, x0=x0, y0=y0: (x0 + (bb[2] - x), y0 + (bb[3] - y))
    else:
        tr = lambda x, y, bb=bb, x0=x0, y0=y0: (x0 + (x - bb[0]), y0 + (y - bb[1]))
    P[c] = {k: tr(*v) for k, v in labs.items()}
    P[c]["_bbox"] = (x0, y0, x0 + bb[2] - bb[0], y0 + bb[3] - bb[1])
    # getcell places the cell's bounding box with its lower-left corner at the box; '180' rotates it first
    T += [f"box {f(x0)} {f(y0)} {f(x0)} {f(y0)}", f"getcell {c}" + {"R180": " 180", "R90": " 90"}.get(orient, "")]


T += ["select top cell", f"cd {OUT}", f"gds write {OUT}/{TOP}.gds", "quit -noprompt"]
tcl = os.path.join(OUT, "m2p.tcl"); open(tcl, "w").write("\n".join(T) + "\n")
r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", RC, tcl], capture_output=True, text=True, cwd=OUT, stdin=subprocess.DEVNULL)
open(os.path.join(OUT, "m2p.log"), "w").write(r.stdout + r.stderr)
# read back every instance's pin labels in absolute coordinates
l = db.Layout(); l.read(os.path.join(OUT, f"{TOP}.gds")); top = l.cell(TOP)
pins_abs = {}
for inst in top.each_inst():
    c = inst.cell; t = inst.dcplx_trans
    labs = {}
    for li in l.layer_indexes():
        for s in c.shapes(li).each():
            if s.is_text():
                p = t * db.DPoint(s.text.x * l.dbu, s.text.y * l.dbu)
                labs.setdefault(s.text.string, []).append((round(p.x, 3), round(p.y, 3), l.get_info(li).layer))
    bb = inst.dbbox()
    pins_abs[c.name] = {"bbox": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)], "pins": labs}
json.dump(pins_abs, open(os.path.join(OUT, "pins.json"), "w"), indent=0)
print("placed:", ", ".join(f"{k} {v['bbox']}" for k, v in pins_abs.items()))
