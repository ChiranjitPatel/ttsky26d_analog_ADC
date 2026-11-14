#!/usr/bin/env python3
"""M1 — reference chip: top-level integration of the M1 cells on floorplan v3 (Magic).

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
OUT = os.path.join(ROOT, "sim", "out", "layout", "m1")
FP = json.load(open(os.path.join(ROOT, "layout", "floorplan_v3.json")))
CELLS = ["bias_gen", "bandgap_core", "vref_filt", "ptat_out", "vref_sel", "vref_buf"]
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
T += ["load m1_scratch", "edit", f"def read {DEF}", f"cellname rename tt_um_template {TOP}", f"load {TOP}", "edit"]
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
    T += [f"box {f(x0)} {f(y0)} {f(x0)} {f(y0)}", f"getcell {c}" + (" 180" if orient == "R180" else "")]

# ---------------------------------------------------------------- signal wiring
W2, W3, W4 = 0.4, 0.5, 0.3
def bus_bottom(c, net):
    return P[c][net][0], P[c]["_bbox"][1] + 0.3            # side buses run down to the block's bottom edge
bias, bg, flt, pt, sel, buf = (P[c] for c in CELLS)

# G1 (bias_gen / bandgap): pd lane 188.6, pbias lane 189.5
yg1_pd, yg1_pb = 188.6, 189.5
# pbias: bias_gen right pin -> met2 down at x 62 -> G1 lane -> bandgap pbias bus top
px, py = bias["pbias"]; xb = 62.0
hwire("metal3", px, xb, py, W3); stack(xb, py, "metal2", "metal3")
vwire("metal2", xb, py, yg1_pb, W2); stack(xb, yg1_pb, "metal2", "metal3")
gx, gy = bg["pbias"]
hwire("metal3", gx, xb, yg1_pb, W3); stack(gx, yg1_pb, "metal2", "metal3"); vwire("metal2", gx, gy, yg1_pb, W2)

# T1 (top): control pins -> R1 (met4 verticals); pd also -> left (bias_gen, bandgap)
R1 = {"nbias": 79.7, "ui_in[3]": 80.45, "uio_in[3]": 81.35, "ui_in[1]": 82.25}   # met4 lines: 0.9 pitch (0.6 via3 pads)
T1 = {"ui_in[3]": 214.95, "ui_in[1]": 215.85, "uio_in[3]": 216.75}
for pin, y in T1.items():
    x, yp = pins[pin]
    paint("metal4", x - 0.15, y - 0.3, x + 0.15, yp - 0.5)                 # met4 from the pin down to the lane
    stack(x, y, "metal3", "metal4")
    xr = R1[pin]
    xl = 6.6 if pin == "ui_in[3]" else xr
    hwire("metal3", xl, x, y, W3)
    stack(xr, y, "metal3", "metal4")
# pd to bias_gen + bandgap: met2 down at x 6.6
x6 = 6.6
stack(x6, T1["ui_in[3]"], "metal2", "metal3")
vwire("metal2", x6, T1["ui_in[3]"], yg1_pd, W2)
bx, by = bias["pd"]; stack(x6, by, "metal2", "metal3"); hwire("metal3", x6, bx, by, W3)
stack(x6, yg1_pd, "metal2", "metal3")
gx, gy = bg["pd"]
hwire("metal3", x6, gx, yg1_pd, W3); stack(gx, yg1_pd, "metal2", "metal3"); vwire("metal2", gx, gy, yg1_pd, W2)

# nbias: bias_gen right pin -> R1 (met2 at x 80.0) -> lane y 65.6 -> vref_buf nbias bus top
nx, ny = bias["nbias"]; xr = R1["nbias"]; yl = 65.6
hwire("metal3", nx, xr, ny, W3); stack(xr, ny, "metal2", "metal3")
vwire("metal2", xr, ny, yl, W2); stack(xr, yl, "metal2", "metal3")
bx, by = buf["nbias"]
hwire("metal3", xr, bx, yl, W3); stack(bx, yl, "metal2", "metal3"); vwire("metal2", bx, by, yl, W2)

# G2 (bandgap / vref_filt): vbg lane 82.1, vgp lane 83.0
yg2_vbg, yg2_vgp = 82.1, 83.0
gx, _ = bg["vbg"]; gyb = P["bandgap_core"]["_bbox"][1] + 0.3
vwire("metal2", gx, gyb, yg2_vbg, W2); stack(gx, yg2_vbg, "metal2", "metal3")
fx, fy = flt["vbg"]
hwire("metal3", gx, fx, yg2_vbg, W3); stack(fx, yg2_vbg, "metal2", "metal3"); vwire("metal2", fx, fy, yg2_vbg, W2)
# vgp: bandgap vgp bus bottom -> G2 lane -> R2 (met2 at x 70) -> G3 lane -> ptat_out vgp (top)
G3 = {"vbg_f": 39.0, "vgp": 39.9, "uio_in[3]": 40.8, "ui_in[1]": 41.7}
gx, _ = bg["vgp"]; xr2 = 70.0
vwire("metal2", gx, gyb, yg2_vgp, W2); stack(gx, yg2_vgp, "metal2", "metal3")
hwire("metal3", xr2, gx, yg2_vgp, W3); stack(xr2, yg2_vgp, "metal2", "metal3")
vwire("metal2", xr2, yg2_vgp, G3["vgp"], W2); stack(xr2, G3["vgp"], "metal2", "metal3")
tx, ty = pt["vgp"]
hwire("metal3", tx, xr2, G3["vgp"], W3); stack(tx, G3["vgp"], "metal2", "metal3"); vwire("metal2", tx, ty, G3["vgp"], W2)

# G3: ref_sel / vref_oe from R1 (met4) to the vref_sel bus tops
for pin, net in (("uio_in[3]", "ref_sel"), ("ui_in[1]", "vref_oe")):
    xr = R1[pin]; y = G3[pin]
    vwire("metal4", xr, T1[pin], y, W4); stack(xr, y, "metal3", "metal4")
    sx, sy = sel[net]
    hwire("metal3", sx, xr, y, W3); stack(sx, y, "metal2", "metal3"); vwire("metal2", sx, sy, y, W2)

# B1 (bottom): VDPWR tie 1.3, BG_PD 2.2, en_buf 3.1, vref 4.0, pad 4.9, vbg_f 5.8, VGND tie 6.7
B1 = {"VDPWR": 1.3, "pd": 2.2, "en_buf": 3.1, "vref": 4.0, "pad": 4.9, "vbg_f": 5.8, "VGND": 6.7}
# BG_PD to vref_sel: R1 met4 (x 80.6) down to B1, lane left to the bg_pd bus bottom
xr = R1["ui_in[3]"]
vwire("metal4", xr, T1["ui_in[3]"], B1["pd"], W4); stack(xr, B1["pd"], "metal3", "metal4")
sx, sy = bus_bottom("vref_sel", "bg_pd")
hwire("metal3", sx, xr, B1["pd"], W3); stack(sx, B1["pd"], "metal2", "metal3"); vwire("metal2", sx, sy, B1["pd"], W2)
# en_buf: vref_sel bus bottom -> lane -> vref_buf en bus bottom
sx, sy = bus_bottom("vref_sel", "en_buf"); bx, by = bus_bottom("vref_buf", "en")
for x, yb in ((sx, sy), (bx, by)):
    vwire("metal2", x, yb, B1["en_buf"], W2); stack(x, B1["en_buf"], "metal2", "metal3")
hwire("metal3", sx, bx, B1["en_buf"], W3)
# vref: vref_sel vref bus bottom -> lane -> vref_buf vref bus bottom
sx, sy = bus_bottom("vref_sel", "vref"); bx, by = bus_bottom("vref_buf", "vref")
for x, yb in ((sx, sy), (bx, by)):
    vwire("metal2", x, yb, B1["vref"], W2); stack(x, B1["vref"], "metal2", "metal3")
hwire("metal3", sx, bx, B1["vref"], W3)
# pad: vref_sel pad bus bottom -> lane -> ua[1] (via3 onto the met4 stub)
sx, sy = bus_bottom("vref_sel", "pad"); ux = pins["ua[1]"][0]
vwire("metal2", sx, sy, B1["pad"], W2); stack(sx, B1["pad"], "metal2", "metal3")
hwire("metal3", sx, ux, B1["pad"], W3); stack(ux, B1["pad"], "metal3", "metal4")
# vbg_f: vref_filt pin (bottom left after the rotation) -> G3 lane -> x 75 -> B1 lane -> vref_buf in bus bottom
fx, fy = flt["vbg_f"]; xd = 75.0
vwire("metal2", fx, fy, G3["vbg_f"], W2); stack(fx, G3["vbg_f"], "metal2", "metal3")
hwire("metal3", fx, xd, G3["vbg_f"], W3); stack(xd, G3["vbg_f"], "metal2", "metal3")
vwire("metal2", xd, G3["vbg_f"], B1["vbg_f"], W2); stack(xd, B1["vbg_f"], "metal2", "metal3")
bx, by = bus_bottom("vref_buf", "in")
hwire("metal3", xd, bx, B1["vbg_f"], W3); stack(bx, B1["vbg_f"], "metal2", "metal3"); vwire("metal2", bx, by, B1["vbg_f"], W2)

# ---------------------------------------------------------------- power
SX = {n: [(x0 + x1) / 2 for m, x0, x1 in FP["stripes"] if m == n] for n in ("VDPWR", "VGND")}
# internal ties: met3 straps along the bottom, via3 up into every stripe of the net
for net in ("VDPWR", "VGND"):
    xs = SX[net]
    hwire("metal3", xs[0] - 0.3, xs[-1] + 0.3, B1[net], W3)
    for x in xs:
        stack(x, B1[net], "metal3", "metal4")
def rail_to_stripe(x_from, y, net, x_stripe, w=0.6):
    """met1 from a block rail at (x_from, y) to a stripe, via stack up to met4 there."""
    hwire("metal1", x_from, x_stripe, y, w); stack(x_stripe, y, "metal1", "metal4")
L_VDD, L_GND, M_VDD, M_GND, R_VDD, R_GND = SX["VDPWR"][0], SX["VGND"][0], SX["VDPWR"][1], SX["VGND"][1], SX["VDPWR"][2], SX["VGND"][2]
# bias_gen: VGND ring bar (bottom) -> left VGND stripe, VDPWR ring (top) -> left VDPWR stripe
x, y = bias["VGND"]; rail_to_stripe(x, y, "VGND", L_GND, w=0.24)      # as wide as bias_gen's rail bars
x, y = bias["VDPWR"]; rail_to_stripe(x, y, "VDPWR", L_VDD, w=0.24)
# bandgap_core: VGND bus (left) -> left VGND stripe, VDPWR bus (right) -> middle VDPWR stripe, at two heights
for y in (110.0, 160.0):
    rail_to_stripe(bg["VGND"][0], y, "VGND", L_GND)
    rail_to_stripe(bg["VDPWR"][0], y, "VDPWR", M_VDD)
# vref_filt (rotated: its VGND bar is on the right) -> middle VGND stripe
x, _ = flt["VGND"]; rail_to_stripe(x, 60.0, "VGND", M_GND)
# ptat_out: VGND -> left VGND stripe; VDPWR pin -> up (met1) above the cell -> left VDPWR stripe
x, y = pt["VGND"]; rail_to_stripe(x, y, "VGND", L_GND)
x, y = pt["VDPWR"]; ytop = P["ptat_out"]["_bbox"][3] + 0.5
vwire("metal1", x, y, ytop, 0.4); rail_to_stripe(x, ytop, "VDPWR", L_VDD)
# vref_sel, vref_buf: rail buses (met1) down to the bottom tie straps
for c in ("vref_sel", "vref_buf"):
    x, yb = bus_bottom(c, "VGND"); vwire("metal1", x, yb, B1["VGND"], 0.4); stack(x, B1["VGND"], "metal1", "metal3")
    x, yb = bus_bottom(c, "VDPWR"); vwire("metal1", x, yb, B1["VDPWR"], 0.4); stack(x, B1["VDPWR"], "metal1", "metal3")

# ---------------------------------------------------------------- write
T += ["select top cell", "box grow c 5um", "drc on", "drc style drc(full)", "drc check", "drc catchup",
      "set n 0", "foreach {r b} [drc listall why] {incr n [llength $b]}", 'puts "DRC_COUNT $n"',
      "set fp [open " + OUT + "/drc.txt w]",
      "foreach {r b} [drc listall why] { puts $fp \"$r: [llength $b]\"; foreach x [lrange $b 0 199] { puts $fp \"    $x\" } }",
      "close $fp", "select top cell",
      f"cd {OUT}", f"save {TOP}", f"gds write {OUT}/{TOP}.gds", f"lef write {OUT}/{TOP}.lef -hide -pinonly",
      "quit -noprompt"]
tcl = os.path.join(OUT, "m1_top.tcl"); open(tcl, "w").write("\n".join(T) + "\n")
r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", RC, tcl], capture_output=True, text=True, cwd=OUT)
open(os.path.join(OUT, "m1_top.log"), "w").write(r.stdout + r.stderr)
m = re.search(r"DRC_COUNT (\d+)", r.stdout)
print("M1 top: Magic DRC", m.group(1) if m else "?", "->", OUT)

# ---------------------------------------------------------------- LVS reference netlist
subs, seen = [], set()
for c in CELLS:
    txt = open(os.path.join(ROOT, "sim", "out", "netlist", f"{c}.spice")).read()
    for sub in re.findall(r"(\.subckt (\S+).*?\n\.ends)", txt, re.S):
        if sub[1] not in seen:
            seen.add(sub[1]); subs.append(sub[0])
ref = ["* LVS reference for the M1 top level (generated by layout/m1_top.py)", *subs, "",
       f".subckt {TOP} VDPWR VGND ui_in[3] ui_in[1] uio_in[3] ua[1]",
       "xb VDPWR VGND ui_in[3] nbias pbias bias_gen",
       "xbg VDPWR VGND pbias ui_in[3] vbg vgp bandgap_core",
       "xpt VDPWR VGND vgp vptat ptat_out",
       "xf VGND vbg vbg_f vref_filt",
       "xbuf VDPWR VGND nbias en_buf vbg_f vref vref_buf",
       "xsel VDPWR VGND uio_in[3] ui_in[1] ui_in[3] vref ua[1] en_buf vref_sel",
       ".ends", ""]
open(os.path.join(ROOT, "layout", "cells", "m1_top_ref.spice"), "w").write("\n".join(ref))

if "--install" in sys.argv:
    for sub, ext in (("gds", "gds"), ("lef", "lef")):          # the .mag needs the block .mag files: not installed
        src = os.path.join(OUT, f"{TOP}.{ext}")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ROOT, sub, f"{TOP}.{ext}"))
    print("installed into gds/, lef/")
