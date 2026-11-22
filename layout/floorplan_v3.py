#!/usr/bin/env python3
"""Floorplan v3 for tt_um_chiranjitpatel_sar_adc (2026-11-14). Writes layout/floorplan_v3.json and
material/layout/floorplan_v3.png. The earlier floorplan (floorplan.py / floorplan.json / floorplan.png,
used by the M0 frame) is left unchanged.

Why v3: the scripted M1 cells (2026-11-12) are larger than the v1/v2 estimates; bandgap_core alone is
71.7 x 104 um. The left column becomes 72 um wide, so the middle VDPWR/VGND stripe pair moves from
x = 64-69 to x = 83-88, and the right (M2) half is 63.5 um wide (x = 90 ... 153.5).

Placed M1 cells use their real GDS outlines (layout/cells/*.gds). M2 blocks are not drawn yet: their
outlines are estimates (cap_dac at a 3 um unit pitch instead of 4). Routing corridors are reserved areas
for the top-level wiring between blocks (block internals already use met2/met3).
Checks: inside the tile, no overlaps (blocks and corridors), >= 1 um between blocks and power stripes.
"""
import json, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 161.00, 225.76
STRIPE_Y = (1.0, 217.0)   # start at y = 1 (TT: within the bottom 10 um) so the bottom power-tie straps can reach them
stripes = [("VDPWR", 1.0, 3.0), ("VGND", 4.0, 6.0),          # left edge
           ("VDPWR", 83.0, 85.0), ("VGND", 86.0, 88.0),      # middle: moved right from 64-69 (v1/v2)
           ("VDPWR", 154.5, 156.5), ("VGND", 157.5, 159.5)]  # right edge, right of the ua[0] route

def gds_size(cell):
    import klayout.db as db
    l = db.Layout(); l.read(os.path.join(ROOT, "layout", "cells", f"{cell}.gds")); b = l.top_cell().bbox()
    return b.width() * l.dbu, b.height() * l.dbu

def at(cell, x, y, orient="R0"):
    w, h = gds_size(cell)
    if orient in ("R90", "R270"):
        w, h = h, w
    return (x, y, round(x + w, 2), round(y + h, 2))

# name: (rect, milestone, status, orientation, note)
blocks = {
    # ---- left column (x 7 ... 78.7) ----
    "bias_gen":     (at("bias_gen", 7.0, 190.5), "M1", "drawn", "R0", "pbias/nbias/pd pins on its sides"),
    "bandgap_core": (at("bandgap_core", 7.0, 84.0), "M1", "drawn", "R0", "OTA + MIM, sources, startup, PNP array, R1/R2"),
    "vref_filt":    (at("vref_filt", 7.0, 42.0, "R180"), "M1", "drawn", "R180", "rotated 180: vbg pin top right (next to the bandgap's vbg), vbg_f bottom left"),
    "ptat_out":     (at("ptat_out", 7.0, 7.0), "M1", "drawn", "R0", "vptat runs along the bottom corridor to the input mux"),
    "vref_sel":     (at("vref_sel", 41.0, 7.0), "M1", "drawn", "R0", "pad (TG) runs along the bottom corridor to ua[1]"),
    # ---- right half (x 90 ... 153.5) ----
    "vref_buf":     (at("vref_buf", 90.0, 7.0), "M1", "drawn", "R0", "vref to vref_sel (bottom corridor) and up to dac_sw"),
    "inmux":        ((135.0, 7.0, 153.5, 53.0), "M2", "estimate", "R0", "VIN from ua[0] (x 152.3); vptat / vbg come in along the bottom corridor"),
    "dac_sw":       ((90.0, 67.0, 153.5, 77.0), "M2", "estimate", "R0", "9 bottom-plate switch cells under the array"),
    "cap_dac":      ((93.0, 80.0, 151.0, 138.0), "M2", "estimate", "R0", "16 x 16 MIM units + dummy ring at a 3 um pitch (v2: 4 um)"),
    "comparator":   ((93.0, 141.0, 121.0, 161.0), "M2", "estimate", "R0", "right above the array: short, shielded vtop"),
    "vcm_gen":      ((123.0, 141.0, 153.5, 163.0), "M2", "estimate", "R0", "next to the comparator's inn"),
    "adc_digital":  ((90.0, 168.0, 153.5, 214.0), "M2", "estimate", "R0", "LibreLane macro, 63.5 x 46 um (was 82 x 30)"),
}
corridors = {  # reserved for top-level routing
    "G1 bias/bandgap":     (7.0, 188.03, 78.7, 190.5),
    "G2 bandgap/vref_filt": (7.0, 81.46, 78.7, 84.0),
    "G3 vref_filt/bottom": (7.0, 38.44, 78.7, 42.0),
    "R1 left column, right edge": (79.5, 7.0, 82.0, 214.4),
    "R2 beside vref_filt":  (60.5, 42.0, 78.7, 81.46),
    "B1 bottom (pads)":     (7.0, 1.6, 153.5, 6.4),
    "T1 top (control pins -> R1)": (7.0, 214.6, 153.5, 216.6),
}

problems = []
def ov(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap
names = list(blocks)
for i, n in enumerate(names):
    r = blocks[n][0]
    if not (0 <= r[0] < r[2] <= W and 5 <= r[1] < r[3] <= H - 9):
        problems.append(f"{n} outside the usable tile {r}")
    for m in names[i + 1:]:
        if ov(r, blocks[m][0]):
            problems.append(f"{n} overlaps {m}")
    for net, x0, x1 in stripes:
        if ov(r, (x0, STRIPE_Y[0], x1, STRIPE_Y[1]), gap=1.0):
            problems.append(f"stripe {net} at x = {x0} is within 1 um of {n}")
    for c, cr in corridors.items():
        if ov(r, cr):
            problems.append(f"corridor '{c}' overlaps {n}")
used = sum((b[0][2] - b[0][0]) * (b[0][3] - b[0][1]) for b in blocks.values())
m1 = sum((b[0][2] - b[0][0]) * (b[0][3] - b[0][1]) for b in blocks.values() if b[1] == "M1")
print(f"{'block':13s} {'x0':>7s} {'y0':>7s} {'x1':>7s} {'y1':>7s}   size")
for n, (r, ms, st, o, note) in blocks.items():
    print(f"{n:13s} {r[0]:7.2f} {r[1]:7.2f} {r[2]:7.2f} {r[3]:7.2f}   {r[2]-r[0]:5.1f} x {r[3]-r[1]:5.1f}  {ms} {st} {o}")
print(f"blocks {used:.0f} um^2 of {W*H:.0f} ({100*used/(W*H):.0f} %), M1 drawn {m1:.0f} um^2")
print("PROBLEMS:" if problems else "checks: OK", *problems, sep="\n  ")
json.dump({"version": 3, "date": "2026-11-14", "tile": [W, H], "stripes": stripes, "stripe_y": STRIPE_Y,
           "blocks": {n: {"rect": list(r), "milestone": ms, "status": st, "orient": o, "note": note}
                      for n, (r, ms, st, o, note) in blocks.items()},
           "corridors": {c: list(r) for c, r in corridors.items()}},
          open(os.path.join(ROOT, "layout", "floorplan_v3.json"), "w"), indent=1)

# ---- picture (new file; the v1/v2 floorplan.png is not touched) ----
fig, ax = plt.subplots(figsize=(8.6, 11.4)); fig.patch.set_facecolor("white")
ax.add_patch(Rectangle((0, 0), W, H, fc="white", ec="black", lw=1.2))
for c, r in corridors.items():
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc="none", ec="#7f7f7f", lw=0.6, hatch="////", alpha=0.6))
for net, x0, x1 in stripes:
    ax.add_patch(Rectangle((x0, STRIPE_Y[0]), x1 - x0, STRIPE_Y[1] - STRIPE_Y[0], fc="#d62728" if net == "VDPWR" else "#444444", alpha=0.7))
col = {("M1", "drawn"): "#9ecae1", ("M2", "estimate"): "#ffe2c4"}
for n, (r, ms, st, o, note) in blocks.items():
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc=col[(ms, st)], ec="#333333", lw=0.9,
                           ls="-" if st == "drawn" else "--"))
    label = f"{n}\n{r[2]-r[0]:.1f} x {r[3]-r[1]:.1f}" + (f"\n{o}" if o != "R0" else "")
    ax.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, label, fontsize=7, ha="center", va="center")
d = open(os.path.join(ROOT, "layout", "tt_analog_1x2.def")).read()
for name, x, y in re.findall(r"- (\S+) \+ NET .*?\+ PLACED \( (\d+) (\d+) \) N ;", d, re.S):
    x, y = int(x) / 1000, int(y) / 1000
    ax.plot(x, y, "s", ms=2.5, color="#d62728" if name.startswith("ua") else "#1f77b4")
for name, x in (("ua[0]\nVIN", 152.26), ("ua[1]\nVREF", 132.94)):
    ax.annotate(name, (x, 0.5), (x - 6, -10), fontsize=7, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5))
for name, x, dx in (("ui[3]\nBG_PD", 130.18, -9), ("ui[1]\nVREF_OE", 135.70, 9), ("uio[3]\nREF_SEL", 108.10, -4)):
    ax.annotate(name, (x, H - 0.5), (x + dx, H + 6), fontsize=6, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5))
ax.text(31, H + 2.5, "outputs (tied to VGND in M0/M1)", fontsize=6)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc="#9ecae1", ec="#333333", label="M1, drawn (real GDS size)"),
                   Patch(fc="#ffe2c4", ec="#333333", ls="--", label="M2, estimate"),
                   Patch(fc="none", ec="#7f7f7f", hatch="////", label="routing corridor"),
                   Patch(fc="#d62728", alpha=0.7, label="VDPWR met4 stripe"),
                   Patch(fc="#444444", alpha=0.7, label="VGND met4 stripe")],
          fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3)
ax.set_xlim(-4, W + 4); ax.set_ylim(-16, H + 14); ax.set_aspect("equal")
ax.set_title("Floorplan v3 (2026-11-14) — tt_um_chiranjitpatel_sar_adc, 1x2 tile 161.00 × 225.76 µm\n"
             "left column 72 µm wide for the scripted bandgap; middle stripes moved to x = 83-88", fontsize=9)
ax.set_xlabel("x [µm]"); ax.set_ylabel("y [µm]")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "material", "layout", "floorplan_v3.png"), dpi=120, facecolor="white")
print("wrote layout/floorplan_v3.json, material/layout/floorplan_v3.png")
