#!/usr/bin/env python3
"""Floorplan for tt_um_chiranjitpatel_sar_adc (chunk 0b). Writes layout/floorplan.json, checks it, renders
material/layout/floorplan.png. Coordinates in um, origin at the tile's bottom-left corner.
Every block's outline is sized from its device-area estimate (layout/area_estimate.py) with room for
routing and guard rings; the 'ratio' column in the check output is outline / device area.
Rules checked: inside the tile, no block overlaps, no power stripe crosses a block, 1 um clearance
between blocks and stripes, MIM array and digital block free of met4 stripes.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 161.00, 225.76
STRIPE_Y = (5.0, 217.0)   # TT: start in the bottom 10 um, reach the top 10 um (>= 215.76); ends below the
                          # output-pin stubs (the middle stripes sit under the uio_out pins at x = 63.9 ... 69.5)
stripes = [  # (net, x0, x1) vertical met4, 2 um wide
    ("VDPWR", 1.0, 3.0), ("VGND", 4.0, 6.0),          # left edge (M0)
    ("VDPWR", 64.0, 66.0), ("VGND", 67.0, 69.0),      # between the left column and the DAC / digital
    ("VDPWR", 154.5, 156.5), ("VGND", 157.5, 159.5),  # right edge, right of the ua[0] route at x = 152.3
]
blocks = {  # name: (x0, y0, x1, y1, milestone, note)
    "adc_digital":  (71, 186, 153, 216, "M2", "SAR logic + pin decoding, LibreLane macro under the top pins"),
    "bias_gen":     (8, 188, 30, 214, "M1", "1 uA reference; pbias/nbias to all analog blocks"),
    "ptat_out":     (34, 188, 62, 214, "M1", "PTAT branch, next to the bandgap's vgp"),
    "bandgap_core": (8, 100, 62, 182, "M1", "incl. OTA, PNP 3x3 array, R1/R2 chains, startup"),
    "vref_filt":    (8, 60, 62, 94, "M1", "1 MOhm + 3.9 pF, directly under the bandgap that feeds it"),
    "reserve_left": (8, 6, 62, 56, "—", "spare: growth / relocation"),
    "reserve_right": (72, 6, 116, 34, "—", "spare, next to the DAC: e.g. a larger reservoir cap"),
    "comparator":   (86, 164, 114, 184, "M2", "directly above the DAC: short, shielded vtop"),
    "vcm_gen":      (116, 164, 150, 184, "M2", "next to the comparator's inn"),
    "cap_dac":      (76, 90, 148, 162, "M2", "16x16 MIM units + dummy ring (18x18 at 4 um pitch); no met4 stripe"),
    "dac_sw":       (76, 78, 148, 88, "M2", "9 bottom-plate switch cells, one under each column group"),
    "vref_buf":     (72, 38, 116, 74, "M1", "incl. 5.4 pF reservoir cap; vref to dac_sw is short"),
        "vref_sel":     (118, 6, 150, 20, "M1", "logic + TG; sits on the ua[1] pin (x = 132.9)"),
    "inmux":        (118, 24, 150, 50, "M2", "VIN from ua[0] (x = 152.3) up the right edge"),
}
est = json.load(open(os.path.join(ROOT, "sim", "out", "area_estimate.json")))
est_map = {"cap_dac": est["cap_dac"] - 9 * est["dac_sw"], "dac_sw": 9 * est["dac_sw"], "adc_digital": 1289 / 0.55}

problems = []
def overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap
names = list(blocks)
for i, n in enumerate(names):
    b = blocks[n]
    if not (0 <= b[0] < b[2] <= W and 5 <= b[1] < b[3] <= H - 5):
        problems.append(f"{n} outside the usable tile")
    for m in names[i + 1:]:
        if overlap(b, blocks[m]):
            problems.append(f"{n} overlaps {m}")
    for net, x0, x1 in stripes:
        if overlap(b, (x0, STRIPE_Y[0], x1, STRIPE_Y[1]), gap=1.0):
            problems.append(f"stripe {net} @ x={x0} too close to / crosses {n}")
print("block          outline   devices  ratio   milestone")
total = 0
for n, b in blocks.items():
    a = (b[2] - b[0]) * (b[3] - b[1]); dv = est_map.get(n, est.get(n, 0)); total += 0 if n.startswith("reserve") else a
    r = f"{a/dv:5.1f}x" if dv else "   —  "
    print(f"{n:13s} {a:7.0f}  {dv:7.0f}  {r}   {b[4]}")
print(f"used {total:.0f} of {W*H:.0f} um^2 ({100*total/(W*H):.0f} %); reserve {sum((b[2]-b[0])*(b[3]-b[1]) for n, b in blocks.items() if n.startswith(chr(114)+chr(101)+chr(115))):.0f} um^2")
print("PROBLEMS:" if problems else "checks: OK", *problems, sep="\n  ")
json.dump({"tile": [W, H], "stripes": stripes, "stripe_y": STRIPE_Y,
           "blocks": {n: {"rect": b[:4], "milestone": b[4], "note": b[5]} for n, b in blocks.items()}},
          open(os.path.join(ROOT, "layout", "floorplan.json"), "w"), indent=1)

# render
col = {"M1": "#cfe8ff", "M2": "#ffe2c4", "—": "#eeeeee"}
fig, ax = plt.subplots(figsize=(8, 11)); fig.patch.set_facecolor("white")
ax.add_patch(Rectangle((0, 0), W, H, fc="white", ec="black", lw=1.2))
for net, x0, x1 in stripes:
    ax.add_patch(Rectangle((x0, STRIPE_Y[0]), x1 - x0, STRIPE_Y[1] - STRIPE_Y[0], fc="#d62728" if net == "VDPWR" else "#444444", alpha=0.7))
    ax.text((x0 + x1) / 2, 112, net, rotation=90, fontsize=6, ha="center", va="center", color="white")
for n, b in blocks.items():
    ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fc=col[b[4]], ec="#333333", lw=0.8))
    ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, f"{n}\n{b[4]}", fontsize=7, ha="center", va="center")
import re
d = open(os.path.join(ROOT, "layout", "tt_analog_1x2.def")).read()
for name, x, y in re.findall(r"- (\S+) \+ NET .*?\+ PLACED \( (\d+) (\d+) \) N ;", d, re.S):
    x, y = int(x) / 1000, int(y) / 1000
    ax.plot(x, y, "s", ms=2.5, color="#d62728" if name.startswith("ua") else "#1f77b4")
for name, x in (("ua[0]\nVIN", 152.26), ("ua[1]\nVREF", 132.94)):
    ax.annotate(name, (x, 0.5), (x - 6, -9), fontsize=7, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5))
ax.text(31, H + 2.5, "uio_oe · uio_out · uo_out (outputs)", fontsize=7); ax.text(97, H + 2.5, "uio_in · ui_in · rst_n · clk", fontsize=7)
ax.set_xlim(-4, W + 4); ax.set_ylim(-14, H + 8); ax.set_aspect("equal")
ax.set_title("Floorplan — tt_um_chiranjitpatel_sar_adc (1x2, 161.00 × 225.76 µm)\nblue: M1 (reference chip), orange: M2 (ADC), red/grey: VDPWR/VGND met4 stripes", fontsize=9)
ax.set_xlabel("x [µm]"); ax.set_ylabel("y [µm]")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "material", "layout", "floorplan.png"), dpi=110, facecolor="white")
