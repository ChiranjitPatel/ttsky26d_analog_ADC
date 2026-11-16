#!/usr/bin/env python3
"""M2 — full ADC chip: top-level integration on floorplan v4 (Magic).

Run layout/m2_place.py first (placement-only build -> sim/out/layout/m2p/pins.json, every pin in absolute
coordinates); this script reads those positions, so no coordinate below is typed in by hand except the
corridor / lane positions. Routing plan: docs/specs/layout_plan.md, "M2 integration plan".
  python3 layout/m2_top.py            build to sim/out/layout/m2 + Magic DRC count + LVS reference netlist
  python3 layout/m2_top.py --install  also copy gds/lef into gds/, lef/ (the submission)
"""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import RC, f

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = "tt_um_chiranjitpatel_sar_adc"
DEF = os.path.join(ROOT, "layout", "tt_analog_1x2.def")
OUT = os.path.join(ROOT, "sim", "out", "layout", "m2")
FP = json.load(open(os.path.join(ROOT, "layout", "floorplan_v4.json")))
PJ = json.load(open(os.path.join(ROOT, "sim", "out", "layout", "m2p", "pins.json")))
CELLS = ["bias_gen", "bandgap_core", "vref_filt", "ptat_out", "vref_sel", "vref_buf",
         "inmux", "vcm_gen", "dac", "comparator", "adc_digital"]
os.makedirs(OUT, exist_ok=True)
for fn in os.listdir(OUT):
    if fn.endswith(".mag") or fn.endswith(".ext"):
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
    i0, i1 = LAYERS.index(lo), LAYERS.index(hi)
    for i in range(i0, i1):
        cut, s, pad = CUTS[(LAYERS[i], LAYERS[i + 1])]
        paint(LAYERS[i], x - pad / 2, y - pad / 2, x + pad / 2, y + pad / 2)
        paint(LAYERS[i + 1], x - pad / 2, y - pad / 2, x + pad / 2, y + pad / 2)
        paint(cut, x - s / 2, y - s / 2, x + s / 2, y + s / 2)
W2, W3, W4 = 0.2, 0.4, 0.4                                    # corridor lines (met2) are 0.2 wide
def via23(x, y):
    """slim met2<->met3 via for the corridor lines: met2 pad 0.4 x 0.57 (via2 0.32 + 0.04 / 0.125), met3 pad 0.45."""
    paint("metal2", x - 0.2, y - 0.285, x + 0.2, y + 0.285)
    paint("via2", x - 0.16, y - 0.16, x + 0.16, y + 0.16)
    paint("metal3", x - 0.225, y - 0.225, x + 0.225, y + 0.225)
def via34(x, y):
    """slim met3<->met4 via: via3 0.32, met3 / met4 pads 0.45."""
    paint("metal3", x - 0.225, y - 0.225, x + 0.225, y + 0.225)
    paint("via3", x - 0.16, y - 0.16, x + 0.16, y + 0.16)
    paint("metal4", x - 0.225, y - 0.225, x + 0.225, y + 0.225)
def pin(c, n):
    return tuple(PJ[c]["pins"][n][0][:2])

# ---------------------------------------------------------------- cells, frame
# the LibreLane macro is kept verbatim (readonly): Magic's regenerated std-cell implants fail the KLayout FEOL deck
T += [("gds readonly true; " if c == "adc_digital" else "") + f"gds read {os.path.join(ROOT, 'layout', 'cells', c + '.gds')}"
      + ("; gds readonly false" if c == "adc_digital" else "") for c in CELLS]
T += ["load m2_scratch", "edit", f"def read {DEF}", f"cellname rename tt_um_template {TOP}", f"load {TOP}", "edit"]
SY0, SY1 = FP["stripe_y"]
EXT = {(86.0, 88.0): 219.9, (1.0, 3.0): 220.7, (4.0, 6.0): 219.9}   # stripes extended upward
for net, x0, x1 in FP["stripes"]:
    T += [f"box {f(x0)} {f(SY0)} {f(x1)} {f(EXT.get((x0, x1), SY1))}", "paint met4", f"label {net} FreeSans 0.25u -met4",
          "port make", f"port use {'ground' if net == 'VGND' else 'power'}", "port class bidirectional", "port connections n s e w"]
d = open(DEF).read()
pins = {n: (int(x) / 1000, int(y) / 1000) for n, x, y in re.findall(r"- (\S+) \+ NET .*?\+ PLACED \( (\d+) (\d+) \) N ;", d, re.S)}
PIN_Y = 224.76
for c in CELLS:
    rect = FP["blocks"][c]["rect"]; orient = FP["blocks"][c]["orient"]
    T += [f"box {f(rect[0])} {f(rect[1])} {f(rect[0])} {f(rect[1])}", f"getcell {c}" + {"R180": " 180", "R90": " 90"}.get(orient, "")]

SX = {n: [(x0 + x1) / 2 for m, x0, x1 in FP["stripes"] if m == n] for n in ("VDPWR", "VGND")}
L_VDD, L_GND, M_VDD, M_GND, R_VDD, R_GND = SX["VDPWR"][0], SX["VGND"][0], SX["VDPWR"][1], SX["VGND"][1], SX["VDPWR"][2], SX["VGND"][2]

# ---------------------------------------------------------------- output pins
# constants tied in metal: uio_oe[5:4] -> VDPWR bar (y 220.35), the other uio_oe and uio_out[7:6,3:0] -> VGND bar (219.5)
TIE_G, TIE_P = 219.5, 220.35
ties_g = [f"uio_oe[{i}]" for i in (7, 6, 3, 2, 1, 0)] + [f"uio_out[{i}]" for i in (7, 6, 3, 2, 1, 0)]
ties_p = ["uio_oe[5]", "uio_oe[4]"]
hwire("metal3", L_GND - 0.6, max(pins[n][0] for n in ties_g) + 0.3, TIE_G, 0.5); stack(L_GND, TIE_G, "metal3", "metal4")
hwire("metal3", L_VDD - 0.6, max(pins[n][0] for n in ties_p) + 0.3, TIE_P, 0.5); stack(L_VDD, TIE_P, "metal3", "metal4")
for n, y in [(n, TIE_G) for n in ties_g] + [(n, TIE_P) for n in ties_p]:
    x = pins[n][0]
    vwire("metal4", x, y, PIN_Y + 0.3, 0.3); stack(x, y, "metal3", "metal4")
for n in ("ua[0]", "ua[1]"):
    x = pins[n][0]; paint("metal4", x - 0.45, 0.0, x + 0.45, 5.4 if n == "ua[1]" else 4.3)

# ---------------------------------------------------------------- digital block: power bars above it, north pins
dg = PJ["adc_digital"]; dgb = dg["bbox"]
DTOP = dgb[3]
BAR_G = DTOP + 0.6                                           # VGND bar (met3) above the block
strap_x = {"VDPWR": [90.0 + c for c in (6.84, 26.84, 46.84)], "VGND": [90.0 + c for c in (9.74, 29.74, 49.74)]}
hwire("metal3", M_GND, max(strap_x["VGND"]) + 0.6, BAR_G, 0.3); stack(M_GND, BAR_G, "metal3", "metal4")
for x in strap_x["VGND"]:
    paint("metal4", x - 0.6, DTOP - 0.5, x + 0.6, BAR_G + 0.3); stack(x, BAR_G, "metal3", "metal4")
# VDPWR: the left strap's bottom end -> met3 along y 171.3 (between the comparator and the block) -> middle stripe
YVP = dgb[1] - 0.3
paint("metal4", strap_x["VDPWR"][0] - 0.6, YVP - 0.3, strap_x["VDPWR"][0] + 0.6, dgb[1] + 0.5)
stack(strap_x["VDPWR"][0], YVP, "metal3", "metal4")
hwire("metal3", M_VDD, strap_x["VDPWR"][0], YVP, 0.3); stack(M_VDD, YVP, "metal3", "metal4")
# north pins: met2 up through the bars, met3 river tracks (left edge packing), via3, met4 up to the TT pin
north = [n for n in dg["pins"] if re.match(r"(uo_out|uio_in|ui_in)\[|rst_n$|clk$", n)]
spans = sorted(((pins[n][0], dg["pins"][n][0][0], n) for n in north), key=lambda t: t[0])
TR0, TRP = BAR_G + 0.9, 0.8
tracks = []                                                  # [(end_x, y)]
assign = {}
for xt, xp, n in sorted(spans, key=lambda t: min(t[0], t[1])):
    lo, hi = min(xt, xp), max(xt, xp)
    for k, end in enumerate(tracks):
        if lo - 0.25 >= end + 0.3:
            tracks[k] = hi + 0.25; assign[n] = k; break
    else:
        tracks.append(hi + 0.25); assign[n] = len(tracks) - 1
for xt, xp, n in spans:
    y = TR0 + TRP * assign[n]
    vwire("metal2", xp, DTOP - 0.1, y, W2); via23(xp, y)
    hwire("metal3", xp, xt, y, 0.3); via34(xt, y)
    vwire("metal4", xt, y, PIN_Y + 0.3, 0.3)
print(f"north pins: {len(spans)} nets on {len(tracks)} tracks, top track y {TR0 + TRP * (len(tracks) - 1):.2f}")

# ---------------------------------------------------------------- digital west pins
# gn/gpb bits 7-4 -> R4 (met2 under the middle stripes) -> met3 jog -> met4 tracks under the dac -> landing pads
dac = PJ["dac"]["pins"]
left = sorted([f"gn{i}" for i in (7, 6, 5, 4)] + [f"gpb{i}" for i in (7, 6, 5, 4)], key=lambda n: dac[n][0][0])
right = sorted([f"gn{i}" for i in (3, 2, 1, 0)] + [f"gpb{i}" for i in (3, 2, 1, 0)], key=lambda n: -dac[n][0][0])
TRK = [62.2 - 0.9 * k for k in range(8)]                     # nearest landing -> highest track (0.9: via3 pads)
R4X = [83.2, 84.6, 85.05, 85.5, 85.95, 86.4, 87.6, 88.05]     # avoids the stripe-centre power stacks (84.0, 87.0)
XT_L = 88.6                                                  # met4 tracks start right of the VGND stripe
dname = lambda n: n[:-1].replace("gn", "gn[").replace("gpb", "gpb[") + n[-1] + "]"
for k, n in enumerate(left):
    py = dg["pins"][dname(n)][0][1]
    xc = R4X[k]
    hwire("metal3", dgb[0] + 0.3, xc, py, 0.3); via23(xc, py)
    vwire("metal2", xc, py, TRK[k], W2); via23(xc, TRK[k])
    hwire("metal3", xc, XT_L, TRK[k], 0.3); stack(XT_L, TRK[k], "metal3", "metal4")
    paint("metal3", xc - 0.225, TRK[k] - 0.3, XT_L, TRK[k] + 0.3)          # no notch between the two pads
    lx, ly = dac[n][0][:2]
    hwire("metal4", XT_L, lx, TRK[k], 0.3); vwire("metal4", lx, TRK[k], ly, 0.3)
# control: ref_sel / vref_oe / bg_pd -> the R1 met4 lines (x 81.35 / 82.25 / 80.45), as in M1 below that
R1 = {"bg_pd": 80.45, "ref_sel": 81.35, "vref_oe": 82.25}
CTL_Y = {n: dg["pins"][n][0][1] for n in ("ref_sel", "vref_oe")}
CTL_Y["bg_pd"] = 204.6                                       # below bias_gen's nbias row (205.365)
for net, xr in R1.items():
    py = dg["pins"][net][0][1]; yc = CTL_Y[net]
    if abs(py - yc) > 0.01:
        hwire("metal3", dgb[0] + 0.3, 88.6, py, 0.3); via23(88.6, py)
        vwire("metal2", 88.6, py, yc, W2); via23(88.6, yc)
        hwire("metal3", 88.6, xr, yc, 0.3)
    else:
        hwire("metal3", dgb[0] + 0.3, xr, yc, 0.3)
    via34(xr, yc)
G3 = {"vbg_f": 39.0, "vgp": 39.9, "ref_sel": 40.8, "vref_oe": 41.7}
B1 = {"VDPWR": 1.3, "pd": 2.2, "en_buf": 3.1, "vref": 4.0, "pad": 4.9, "vbg_f": 5.8, "VGND": 6.7}
sel = {k: v[0][:2] for k, v in PJ["vref_sel"]["pins"].items()}
for net in ("ref_sel", "vref_oe"):
    xr = R1[net]; y = G3[net]
    vwire("metal4", xr, CTL_Y[net], y, W4); stack(xr, y, "metal3", "metal4")
    sx, sy = sel[net]
    hwire("metal3", sx, xr, y, 0.5); stack(sx, y, "metal2", "metal3"); vwire("metal2", sx, sy, y, 0.4)
# bg_pd: R1 line down to B1 (vref_sel) and, at G1, left to the bandgap's pd bus
xr = R1["bg_pd"]
vwire("metal4", xr, CTL_Y["bg_pd"], B1["pd"], W4); stack(xr, B1["pd"], "metal3", "metal4")
sbx = PJ["vref_sel"]["bbox"]
sx = sel["bg_pd"][0]; sy = sbx[1] + 0.3
hwire("metal3", sx, xr, B1["pd"], 0.5); stack(sx, B1["pd"], "metal2", "metal3"); vwire("metal2", sx, sy, B1["pd"], 0.4)
yg1_pd, yg1_pb = 188.6, 189.5
stack(xr, yg1_pd, "metal3", "metal4")
gx, gy = pin("bandgap_core", "pd")
hwire("metal3", gx, xr, yg1_pd, 0.5); stack(gx, yg1_pd, "metal2", "metal3"); vwire("metal2", gx, gy, yg1_pd, 0.4)
# eoc / cmp_out -> uio_out[5] / uio_out[4]: left above bias_gen, met4 up to the pins
for net, tt, y in (("eoc", "uio_out[5]", 215.8), ("cmp_out", "uio_out[4]", 216.6)):
    py = dg["pins"][net][0][1]; xj = 89.15 if net == "eoc" else 88.55
    hwire("metal3", dgb[0] + 0.3, xj, py, 0.3); via23(xj, py)
    vwire("metal2", xj, py, y, W2); via23(xj, y)
    xt = pins[tt][0]
    hwire("metal3", xj, xt, y, 0.3); stack(xt, y, "metal3", "metal4"); vwire("metal4", xt, y, PIN_Y + 0.3, 0.3)

# ---------------------------------------------------------------- R3 (under the right stripes): all met2 verticals
R3X = [153.75 + 0.44 * k for k in range(16)]
r3 = {}
order = ["vptat", "vbg", "vin"] + right + ["smp", "smpb", "vadc", "vcm"]
# keep the three that go to the very bottom off the B1 tie stacks (x 155.5 / 158.5): they take the first slots
for k, n in enumerate(order):
    r3[n] = R3X[k]
# right-group gn/gpb: east pins -> R3 -> met3 jog -> met4 tracks (left) -> landing pads
XT_R = 153.6                                                 # pad clears vcm_gen's met3 buses (152.91) and the stripe (154.5)
for k, n in enumerate(right):
    py = dg["pins"][dname(n)][0][1]; xv = r3[n]
    hwire("metal3", dgb[2] - 0.3, xv, py, 0.3); via23(xv, py)
    vwire("metal2", xv, py, TRK[k], W2); via23(xv, TRK[k])
    hwire("metal3", xv, XT_R, TRK[k], 0.3); stack(XT_R, TRK[k], "metal3", "metal4")
    lx, ly = dac[n][0][:2]
    hwire("metal4", XT_R, lx, TRK[k], 0.3); vwire("metal4", lx, TRK[k], ly, 0.3)
# smp / smpb: east pins -> R3 -> met3 jog -> met4 (y 65.0 / 67.5) -> stack onto the dac's right-end pads
for n in ("smp", "smpb"):
    yj = dac[n][0][1]                                        # straight in at the pad height
    py = dg["pins"][n][0][1]; xv = r3[n]
    hwire("metal3", dgb[2] - 0.3, xv, py, 0.3); via23(xv, py)
    vwire("metal2", xv, py, yj, W2); via23(xv, yj)
    hwire("metal3", xv, XT_R, yj, 0.3); stack(XT_R, yj, "metal3", "metal4")
    lx, ly = dac[n][0][:2]
    hwire("metal4", XT_R, lx, yj, 0.3); stack(lx, ly, "metal1", "metal4")
# vadc: inmux strap -> R3 -> met3 -> met4 (y 66.165) -> stack onto the dac's vadc line (met2) at x 149.5
im = {k: v[0][:2] for k, v in PJ["inmux"]["pins"].items()}
def inmux_to_r3(n):
    x, y = im[n]; xv = r3[n]
    hwire("metal3", x, xv, y, 0.3); stack(x, y, "metal2", "metal3"); via23(xv, y)
    return xv, y
xv, y = inmux_to_r3("vadc")
yv = dac["vadc"][0][1]; ya = 69.0                         # approach above smpb (the smp pad leaves no room at yv)
vwire("metal2", xv, y, ya, W2); via23(xv, ya)
hwire("metal3", xv, XT_R, ya, 0.3); stack(XT_R, ya, "metal3", "metal4")
hwire("metal4", XT_R, 149.5, ya, 0.3); vwire("metal4", 149.5, ya, yv, 0.3); stack(149.5, yv, "metal2", "metal4")
# vin: inmux -> R3 -> down to y 4.0 -> met3 left -> via3 onto the ua[0] stub
xv, y = inmux_to_r3("vin")
vwire("metal2", xv, y, 4.0, W2); via23(xv, 4.0)
ux = pins["ua[0]"][0]
hwire("metal3", ux, xv, 4.0, 0.3); stack(ux, 4.0, "metal3", "metal4")
# vptat (met3) / vbg (met2) along the very bottom (y 0.5) from the left column
YB = 0.5
# vptat on met2 along the bottom (its descent at x 7.2 is met2 too); vbg on met3 above it (descends at x 6.55)
xv, y = inmux_to_r3("vptat")
vwire("metal2", xv, y, YB, W2)
px, py = pin("ptat_out", "vptat")
vwire("metal2", px, py, YB, W2)
hwire("metal2", px, xv, YB, W2)
xv, y = inmux_to_r3("vbg")
vwire("metal2", xv, y, YB, W2); via23(xv, YB)
XVBG = 6.55
hwire("metal3", XVBG, xv, YB, 0.3); stack(XVBG, YB, "metal2", "metal3")
# vbg source: the bandgap's vbg bus (G2 lane y 82.1, as in M1) -> met2 down the left edge at x 6.55
gx, _ = pin("bandgap_core", "vbg"); gyb = PJ["bandgap_core"]["bbox"][1] + 0.3
yg2_vbg, yg2_vgp = 82.1, 83.0
vwire("metal2", gx, gyb, yg2_vbg, 0.4); stack(gx, yg2_vbg, "metal2", "metal3")
fx, fy = pin("vref_filt", "vbg")
hwire("metal3", XVBG, fx, yg2_vbg, 0.5); stack(fx, yg2_vbg, "metal2", "metal3"); vwire("metal2", fx, fy, yg2_vbg, 0.4)
stack(XVBG, yg2_vbg, "metal2", "metal3"); vwire("metal2", XVBG, yg2_vbg, YB, W2)
# vcm: vcm_gen pin -> R3 -> up to the comparator's inn bus (right end)
vx, vy = pin("vcm_gen", "vcm"); xv = r3["vcm"]
hwire("metal3", vx, xv, vy, 0.3); stack(vx, vy, "metal2", "metal3"); via23(xv, vy)
cx, cy = pin("comparator", "inn")
vwire("metal2", xv, vy, cy, W2); via23(xv, cy)
hwire("metal3", cx, xv, cy, 0.3); stack(cx, cy, "metal2", "metal3")
# pbias: bias_gen -> (M1: G1 lane to the bandgap) and -> comparator pbias bus (left end, via the T-region)
#        comparator pbias bus (right end) -> R3 -> down to y 63.8 -> vcm_gen pbias
bx, by = pin("bias_gen", "pbias")
xb = 62.0
hwire("metal3", bx, xb, by, 0.5); stack(xb, by, "metal2", "metal3")
vwire("metal2", xb, by, yg1_pb, 0.4); stack(xb, yg1_pb, "metal2", "metal3")
gx, gy = pin("bandgap_core", "pbias")
hwire("metal3", gx, xb, yg1_pb, 0.5); stack(gx, yg1_pb, "metal2", "metal3"); vwire("metal2", gx, gy, yg1_pb, 0.4)
cpx, cpy = pin("comparator", "pbias")
# from bias_gen's pin row (y 207.165) right on met3 to x 89.4, down past the comparator's pbias row (left end)
# and the dac's left edge to y 63.9, then right under the dac to vcm_gen's pbias pin
xpb, YPB = 89.4, 63.9
hwire("metal3", bx, xpb, by, 0.3); via23(xpb, by)
vwire("metal2", xpb, by, YPB, W2); via23(xpb, cpy); via23(xpb, YPB)
hwire("metal3", xpb, PJ["comparator"]["bbox"][0] + 0.5, cpy, 0.3)
stack(PJ["comparator"]["bbox"][0] + 0.5, cpy, "metal2", "metal3")
vpx, vpy = pin("vcm_gen", "pbias")
hwire("metal3", xpb, vpx, YPB, 0.3); stack(vpx, YPB, "metal2", "metal3"); vwire("metal2", vpx, vpy, YPB, W2)

# ---------------------------------------------------------------- comparator <-> digital south pins, inmux enables
for n, cn in (("smpt", "smpt"), ("cmp_clkb", "clkb"), ("opb", "opb"), ("onb", "onb")):
    px, py = dg["pins"][n][0][:2]; cx, cy = pin("comparator", cn)
    vwire("metal2", px, py, cy, W2); stack(px, cy, "metal2", "metal3")
    hwire("metal3", cx, px, cy, 0.3); stack(cx, cy, "metal2", "metal3")
JOG = [171.05 - 0.75 * k for k in range(8)]                        # rightmost net jogs lowest
for k, (dn, inn) in enumerate([(f"en[{i}]", f"en{i}") for i in range(4)] + [(f"enb[{i}]", f"en{i}b") for i in range(4)]):
    px, py = dg["pins"][dn][0][:2]; ix, iy = im[inn]
    yj = JOG[k]
    vwire("metal2", px, py, yj, W2); via23(px, yj)
    hwire("metal3", px, ix, yj, 0.3); via23(ix, yj)
    vwire("metal2", ix, yj, iy, W2); stack(ix, iy, "metal1", "metal2")

# ---------------------------------------------------------------- vtop, vref, nbias
vx, vy = dac["vtop"][0][:2]; cx, cy = pin("comparator", "inp")
vwire("metal4", vx, vy, cy, 0.5); stack(vx, cy, "metal2", "metal4")
rx, ry = pin("vref_buf", "vref")
xr2 = 128.5; yv = dac["vref"][0][1]
stack(rx, ry, "metal2", "metal3"); hwire("metal3", rx, xr2, ry, 0.3); via34(xr2, ry)   # met3 under the gn1/gpb1 met4 drops
vwire("metal4", xr2, ry, yv, 0.3); stack(xr2, yv, "metal2", "metal4")
nx, ny = pin("bias_gen", "nbias"); xn = 79.7; yl = 63.0
hwire("metal3", nx, xn, ny, 0.5); stack(xn, ny, "metal2", "metal3")
vwire("metal2", xn, ny, yl, 0.4); stack(xn, yl, "metal2", "metal3")
bx, by = pin("vref_buf", "nbias")
hwire("metal3", xn, bx, yl, 0.3); via23(bx, yl); vwire("metal2", bx, by, yl, W2)

# ---------------------------------------------------------------- M1 analog wiring (as in m1_top.py)
bg = {k: v[0][:2] for k, v in PJ["bandgap_core"]["pins"].items()}
flt = {k: v[0][:2] for k, v in PJ["vref_filt"]["pins"].items()}
pt = {k: v[0][:2] for k, v in PJ["ptat_out"]["pins"].items()}
buf = {k: v[0][:2] for k, v in PJ["vref_buf"]["pins"].items()}
gx, _ = bg["vgp"]; xr2 = 70.0
vwire("metal2", gx, gyb, yg2_vgp, 0.4); stack(gx, yg2_vgp, "metal2", "metal3")
hwire("metal3", xr2, gx, yg2_vgp, 0.5); stack(xr2, yg2_vgp, "metal2", "metal3")
vwire("metal2", xr2, yg2_vgp, G3["vgp"], 0.4); stack(xr2, G3["vgp"], "metal2", "metal3")
tx, ty = pt["vgp"]
hwire("metal3", tx, xr2, G3["vgp"], 0.5); stack(tx, G3["vgp"], "metal2", "metal3"); vwire("metal2", tx, ty, G3["vgp"], 0.4)
def bus_bottom(c, net):
    return PJ[c]["pins"][net][0][0], PJ[c]["bbox"][1] + 0.3
sx, sy = bus_bottom("vref_sel", "en_buf"); bx, by = bus_bottom("vref_buf", "en")
for x, yb in ((sx, sy), (bx, by)):
    vwire("metal2", x, yb, B1["en_buf"], 0.4); stack(x, B1["en_buf"], "metal2", "metal3")
hwire("metal3", sx, bx, B1["en_buf"], 0.5)
sx, sy = bus_bottom("vref_sel", "vref"); bx, by = bus_bottom("vref_buf", "vref")
for x, yb in ((sx, sy), (bx, by)):
    vwire("metal2", x, yb, B1["vref"], 0.4); stack(x, B1["vref"], "metal2", "metal3")
hwire("metal3", sx, bx, B1["vref"], 0.5)
sx, sy = bus_bottom("vref_sel", "pad"); ux = pins["ua[1]"][0]
vwire("metal2", sx, sy, B1["pad"], 0.4); stack(sx, B1["pad"], "metal2", "metal3")
hwire("metal3", sx, ux, B1["pad"], 0.5); stack(ux, B1["pad"], "metal3", "metal4")
fx, fy = flt["vbg_f"]; xd = 75.0
vwire("metal2", fx, fy, G3["vbg_f"], 0.4); stack(fx, G3["vbg_f"], "metal2", "metal3")
hwire("metal3", fx, xd, G3["vbg_f"], 0.5); stack(xd, G3["vbg_f"], "metal2", "metal3")
vwire("metal2", xd, G3["vbg_f"], B1["vbg_f"], 0.4); stack(xd, B1["vbg_f"], "metal2", "metal3")
bx, by = bus_bottom("vref_buf", "in")
hwire("metal3", xd, bx, B1["vbg_f"], 0.5); stack(bx, B1["vbg_f"], "metal2", "metal3"); vwire("metal2", bx, by, B1["vbg_f"], 0.4)

# ---------------------------------------------------------------- power
for net in ("VDPWR", "VGND"):
    xs = SX[net]
    hwire("metal3", xs[0] - 0.3, xs[-1] + 0.3, B1[net], 0.5)
    for x in xs:
        stack(x, B1[net], "metal3", "metal4")
def rail_to_stripe(x_from, y, x_stripe, w=0.6):
    hwire("metal1", x_from, x_stripe, y, w); stack(x_stripe, y, "metal1", "metal4")
bias = {k: v[0][:2] for k, v in PJ["bias_gen"]["pins"].items()}
x, y = bias["VGND"]; rail_to_stripe(x, y, L_GND, w=0.24)
x, y = bias["VDPWR"]; rail_to_stripe(x, y, L_VDD, w=0.24)
# bias_gen pd -> VGND (the bias stays on: vcm_gen needs it with BG_PD = 1)
x, y = bias["pd"]; hwire("metal3", L_GND, x, y, 0.4); stack(L_GND, y, "metal3", "metal4")
for y in (110.0, 160.0):
    rail_to_stripe(bg["VGND"][0], y, L_GND)
    rail_to_stripe(bg["VDPWR"][0], y, M_VDD)
x, _ = flt["VGND"]; rail_to_stripe(x, 50.0, M_GND)               # below the left gn/gpb tracks
x, y = pt["VGND"]; rail_to_stripe(x, y, L_GND)
x, y = pt["VDPWR"]; ytop = PJ["ptat_out"]["bbox"][3] + 0.5
vwire("metal1", x, y, ytop, 0.4); rail_to_stripe(x, ytop, L_VDD)
for c in ("vref_sel", "vref_buf"):
    x, yb = bus_bottom(c, "VGND"); vwire("metal1", x, yb, B1["VGND"], 0.4); stack(x, B1["VGND"], "metal1", "metal3")
    x, yb = bus_bottom(c, "VDPWR"); vwire("metal1", x, yb, B1["VDPWR"], 0.4); stack(x, B1["VDPWR"], "metal1", "metal3")
# vcm_gen: its rail buses down to the bottom ties
vg = {k: v[0][:2] for k, v in PJ["vcm_gen"]["pins"].items()}
vby = PJ["vcm_gen"]["bbox"][1] + 0.3
x, _ = vg["VGND"]; vwire("metal1", x, vby, B1["VGND"], 0.4); stack(x, B1["VGND"], "metal1", "metal3")
x, _ = vg["VDPWR"]; vwire("metal1", x, vby, B1["VDPWR"], 0.4); stack(x, B1["VDPWR"], "metal1", "metal3")
# dac: switch-row rails (left end) -> middle stripes
x, y = dac["VDPWR"][0][:2]; rail_to_stripe(x, y, M_VDD)
x, y = dac["VGND"][0][:2]; rail_to_stripe(x, y, M_GND)
# comparator: VGND bus (top) <- digital VGND strap 119.74; VDPWR bus (bottom) <- digital VDPWR strap 116.84
cgx, cgy = pin("comparator", "VGND"); cvx, cvy = pin("comparator", "VDPWR")
xs_g, xs_p = strap_x["VGND"][2], strap_x["VDPWR"][1]
# met1 to x 139.9, up to y 171.3 (clear of the en jogs), stack onto the inmux's met4 extension of strap 139.74
hwire("metal1", cgx - 0.2, 139.9, cgy, 0.3); vwire("metal1", 139.9, cgy, 171.3, 0.44); stack(139.9, 171.3, "metal1", "metal4")
paint("metal4", xs_p - 0.6, cvy, xs_p + 0.6, dgb[1] + 0.5); stack(xs_p, cvy, "metal1", "metal4")
# inmux: VGND column <- digital VGND strap 139.74 (met1 across the NMOS top region); VDPWR column <- strap 136.84 (met3)
ib = PJ["inmux"]["bbox"]
ig, iv = im["VGND"], im["VDPWR"]
xs_g, xs_p = strap_x["VGND"][2], strap_x["VDPWR"][2]
yg_ = ib[1] + 3.35 + 4.6; yp_ = ib[1] + 3.35 + 6.0           # inmux local y 4.6 (above the NMOS) / 6.0
vwire("metal1", ib[0] + 0.25, ib[1] + 3.35 + 3.5, yg_, 0.34)
hwire("metal1", ib[0] + 0.25, xs_g, yg_, 0.3); stack(xs_g, yg_, "metal1", "metal4")
paint("metal4", xs_g - 0.6, yg_, xs_g + 0.6, dgb[1] + 0.5)
stack(iv[0], yp_, "metal1", "metal3"); hwire("metal3", iv[0], xs_p, yp_, 0.3); stack(xs_p, yp_, "metal3", "metal4")
paint("metal4", xs_p - 0.6, yp_, xs_p + 0.6, dgb[1] + 0.5)

# ---------------------------------------------------------------- write
T += ["select top cell", "box grow c 5um", "drc on", "drc style drc(full)", "drc check", "drc catchup",
      "set n 0", "foreach {r b} [drc listall why] {incr n [llength $b]}", 'puts "DRC_COUNT $n"',
      "set fp [open " + OUT + "/drc.txt w]",
      "foreach {r b} [drc listall why] { puts $fp \"$r: [llength $b]\"; foreach x [lrange $b 0 199] { puts $fp \"    $x\" } }",
      "close $fp", "select top cell",
      f"cd {OUT}", f"save {TOP}", f"gds write {OUT}/{TOP}.gds", f"lef write {OUT}/{TOP}.lef -hide -pinonly",
      "quit -noprompt"]
tcl = os.path.join(OUT, "m2_top.tcl"); open(tcl, "w").write("\n".join(T) + "\n")
r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", RC, tcl], capture_output=True, text=True, cwd=OUT, stdin=subprocess.DEVNULL)
open(os.path.join(OUT, "m2_top.log"), "w").write(r.stdout + r.stderr)
m = re.search(r"DRC_COUNT (\d+)", r.stdout)
print("M2 top: Magic DRC", m.group(1) if m else "?", "->", OUT)

# ---------------------------------------------------------------- LVS reference netlist
subs, seen = [], set()
for c in ["bias_gen", "bandgap_core", "vref_filt", "ptat_out", "vref_sel", "vref_buf", "inmux", "vcm_gen", "dac", "comparator"]:
    txt = open(os.path.join(ROOT, "sim", "out", "netlist", f"{c}.spice")).read()
    for sub in re.findall(r"(\.subckt (\S+).*?\n\.ends)", txt, re.S):
        if sub[1] not in seen:
            seen.add(sub[1]); subs.append(sub[0])
dig = open(os.path.join(ROOT, "layout", "digital", "adc_digital.spice")).read()
dig = dig[dig.index(".subckt adc_digital"):]
dig = dig[:dig.index(".ends") + 5]
std = os.path.join(os.environ.get("PDK_ROOT", "/usr/local/share/pdk"), "sky130A", "libs.ref", "sky130_fd_sc_hd", "spice", "sky130_fd_sc_hd.spice")
tiein = "uio_out[4] uio_out[5]"          # the 16 constant outputs are tied in metal (not in the reference, as in M1)
ref = ["* LVS reference for the M2 top level (generated by layout/m2_top.py)", f".include {std}", *subs, dig, "",
       f".subckt {TOP} VDPWR VGND " + " ".join(f"ui_in[{i}]" for i in range(8)) + " " + " ".join(f"uio_in[{i}]" for i in range(8))
       + " " + " ".join(f"uo_out[{i}]" for i in range(8)) + f" {tiein} clk rst_n ua[0] ua[1]",
       "xb VDPWR VGND VGND nbias pbias bias_gen",
       "xbg VDPWR VGND pbias bg_pd vbg vgp bandgap_core",
       "xpt VDPWR VGND vgp vptat ptat_out",
       "xf VGND vbg vbg_f vref_filt",
       "xbuf VDPWR VGND nbias en_buf vbg_f vref vref_buf",
       "xsel VDPWR VGND ref_sel vref_oe bg_pd vref ua[1] en_buf vref_sel",
       "xmux VDPWR VGND en0 en1 en2 en3 en0b en1b en2b en3b ua[0] vptat vbg vadc inmux",
       "xvcm VDPWR VGND pbias vcm vcm_gen",
       "xdac VDPWR VGND vref vadc smp smpb " + " ".join(f"gn{i}" for i in range(8)) + " " + " ".join(f"gpb{i}" for i in range(8)) + " vtop dac",
       "xcmp VDPWR VGND pbias cmp_clkb smpt vtop vcm opb onb comparator",
       ]
# adc_digital instance in its .subckt port order
pord = re.search(r"\.subckt adc_digital (.*?)\n(?!\+)", dig, re.S).group(1).replace("\n+", " ").split()
conn = {"VDPWR": "VDPWR", "VGND": "VGND", "bg_pd": "bg_pd", "clk": "clk", "rst_n": "rst_n", "cmp_clkb": "cmp_clkb",
        "cmp_out": "uio_out[4]", "eoc": "uio_out[5]", "onb": "onb", "opb": "opb", "ref_sel": "ref_sel", "vref_oe": "vref_oe",
        "smp": "smp", "smpb": "smpb", "smpt": "smpt"}
conn.update({f"en[{i}]": f"en{i}" for i in range(4)}); conn.update({f"enb[{i}]": f"en{i}b" for i in range(4)})
conn.update({f"gn[{i}]": f"gn{i}" for i in range(8)}); conn.update({f"gpb[{i}]": f"gpb{i}" for i in range(8)})
for i in range(8):
    conn.update({f"ui_in[{i}]": f"ui_in[{i}]", f"uio_in[{i}]": f"uio_in[{i}]", f"uo_out[{i}]": f"uo_out[{i}]"})
ref.append("xdig " + " ".join(conn[p] for p in pord) + " adc_digital")
ref += [".ends", ""]
open(os.path.join(ROOT, "layout", "cells", "m2_top_ref.spice"), "w").write("\n".join(ref))

if "--install" in sys.argv:
    for sub, ext in (("gds", "gds"), ("lef", "lef")):
        src = os.path.join(OUT, f"{TOP}.{ext}")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ROOT, sub, f"{TOP}.{ext}"))
    print("installed into gds/, lef/")
