#!/usr/bin/env python3
"""Chunk 1c — bandgap R1 / R2 unit-resistor array (scripted).

23 strips of res_xhigh_po_0p69, L = 4 um each (generated as one PDK array with a common guard ring;
0.69/4 since the Phase 2 Monte Carlo, 2026-11-08: 4x the area of 0.35/2, same resistance):
    index:  0   1 .. 21   22
            D   21 active   D          D = dummy (both ends and the body on VGND)
Active positions p = 0 .. 20 (array index p + 1): R1 (2 units) at p = 5 and 15, R2 (19 units) on the
rest. The R1 and R2 centroids both sit at p = 10, so a linear gradient doesn't change R2/R1.
    R2: vbg -> 19 units in series (serpentine) -> vq3; skips over the R1 strips on met2 jumpers
    R1: vb -> p5 -> (met3 link, top) -> p15 -> vq2
Pins: vbg, vb, vq2 at the bottom (met2 / met3), vq3 at the top (met2), VGND (met1, left).
The generator's 'l' includes the contact overlap: l = L + 0.16 extracts as L (= the schematic).
All positions come from probing the PDK generator (magic_lib.probe_gencell).
Writes layout/cells/bg_res.gds and the LVS reference layout/cells/bg_res_ref.spice.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, CELLS, probe_gencell

N_ACT = 21
R1_POS = (5, 15)
W_U, L_U = 0.69, 4.0                                  # unit resistor (schematic: res_xhigh_po_0p69, L = 4)
DEV = "sky130_fd_pr__res_xhigh_po_0p69"
_g = probe_gencell(DEV, w=W_U, l=L_U + 0.16, nx=N_ACT + 2, guard=1)
_bb = _g["bbox"]
X0 = _g["labels"]["R1_0"][0]                          # x of array index 0
PITCH = _g["labels"]["R1_1"][0] - X0
YT = _g["labels"]["R1_0"][1] - 0.31                   # inside the top head's met1
YB = _g["labels"]["R2_0"][1] + 0.26                   # inside the bottom head's met1
RING_L, RING_B = _bb[0] + 0.265, _bb[1] + 0.265       # guard-ring centre lines
RING_R, RING_T = _bb[2] - 0.265, _bb[3] - 0.265

def x(p):                       # active position -> strip centre x
    return X0 + PITCH * (p + 1)

L = Layout("bg_res")
L.gencell(DEV, "R", 0, 0, w=W_U, l=L_U + 0.16, nx=N_ACT + 2, guard=1)

def head_via(p, top, hi):
    """met1 pad + via up to `hi` on a strip head."""
    y = YT if top else YB
    L.paint("metal1", x(p) - 0.25, y - 0.25, x(p) + 0.25, y + 0.25)
    L.paint("via1", x(p) - 0.15, y - 0.15, x(p) + 0.15, y + 0.15)
    L.paint("metal2", x(p) - 0.28, y - 0.28, x(p) + 0.28, y + 0.28)
    if hi == "metal3":
        L.paint("via2", x(p) - 0.16, y - 0.16, x(p) + 0.16, y + 0.16)
        L.paint("metal3", x(p) - 0.33, y - 0.33, x(p) + 0.33, y + 0.33)

# R2 serpentine
order = [p for p in range(N_ACT) if p not in R1_POS]
for k in range(len(order) - 1):
    a, b = order[k], order[k + 1]
    top = (k % 2 == 0)
    y = YT if top else YB
    if b - a == 1:                                    # neighbours: met1 bridge between the heads
        L.paint("metal1", x(a) - 0.125, y - 0.15, x(b) + 0.125, y + 0.15)
    else:                                             # skip over an R1 strip: met2 jumper outside the ring
        yj = RING_T + 0.9 if top else RING_B - 0.9
        head_via(a, top, "metal2"); head_via(b, top, "metal2")
        L.wire("metal2", x(a), y, x(a), yj, 0.3)
        L.wire("metal2", x(b), y, x(b), yj, 0.3)
        L.wire("metal2", x(a), yj, x(b), yj, 0.3)
first_top = False                                     # link 0 is on top, so the chain starts at the bottom
last_top = (len(order) - 2) % 2 == 1                  # the end is opposite the last link
YPB = RING_B - 2.2                                    # bottom pin row
# vbg: start of R2, bottom head of order[0], met2 down
head_via(order[0], first_top, "metal2")
L.wire("metal2", x(order[0]), YB, x(order[0]), YPB, 0.3)
L.pin("vbg", "metal2", x(order[0]) - 0.15, YPB - 0.3, x(order[0]) + 0.15, YPB, 1)
# vq3: end of R2, top head of order[-1], met2 up
assert last_top
YPT = RING_T + 3.0
head_via(order[-1], True, "metal2")
L.wire("metal2", x(order[-1]), YT, x(order[-1]), YPT, 0.3)
L.pin("vq3", "metal2", x(order[-1]) - 0.15, YPT, x(order[-1]) + 0.15, YPT + 0.3, 2)

# R1: top heads linked on met3 above the met2 jumpers; bottom heads are the pins vb / vq2 (met3 down)
a, b = R1_POS
yl = RING_T + 1.9
for p in R1_POS:
    head_via(p, True, "metal3")
    L.wire("metal3", x(p), YT, x(p), yl, 0.4)
L.wire("metal3", x(a), yl, x(b), yl, 0.4)
for p, net, idx in ((a, "vb", 3), (b, "vq2", 4)):
    head_via(p, False, "metal3")
    L.wire("metal3", x(p), YB, x(p), YPB, 0.4)
    L.pin(net, "metal3", x(p) - 0.2, YPB - 0.3, x(p) + 0.2, YPB, idx)

# dummies (array index 0 and 22) and VGND: li pad on the guard ring, mcon, met1 bar, stubs to both heads
for side, xi in (("L", X0), ("R", X0 + PITCH * (N_ACT + 1))):
    if side == "L":
        xr0, xr1, xb0, xb1 = RING_L - 0.75, RING_L + 0.085, RING_L - 0.75, RING_L - 0.45
    else:
        xr0, xr1, xb0, xb1 = RING_R - 0.085, RING_R + 0.75, RING_R + 0.45, RING_R + 0.75
    ym = (RING_T + RING_B) / 2
    L.paint("locali", xr0, ym - 0.3, xr1, ym + 0.3)
    xm = (xb0 + xb1) / 2
    L.paint("mcon", xm - 0.085, ym - 0.085, xm + 0.085, ym + 0.085)
    L.paint("metal1", xb0, YB - 0.15, xb1, YT + 0.15)
    for y in (YT, YB):
        lo, hi = sorted((xb0, xi))
        L.paint("metal1", min(xb0, xi - 0.125), y - 0.15, max(xb1, xi + 0.125), y + 0.15)
L.pin("VGND", "metal1", RING_L - 0.75, 3.0, RING_L - 0.45, 4.4, 5)

drc, errs, gds = L.run()
print(f"bg_res: Magic DRC {drc}; {gds}", *errs, sep="\n  ")

lines = ["* LVS reference for layout/cells/bg_res.gds: bandgap R1 (2 units) + R2 (19 units) + 2 dummies",
         "* res_xhigh_po_0p69 pins: P M B", ".subckt bg_res vbg vq3 vb vq2 VGND"]
nets = ["vbg"] + [f"r2_{i}" for i in range(1, 19)] + ["vq3"]
for i in range(19):
    lines.append(f"XR2_{i+1} {nets[i]} {nets[i+1]} VGND sky130_fd_pr__res_xhigh_po_0p69 L=4")
lines += ["XR1_1 vb r1_1 VGND sky130_fd_pr__res_xhigh_po_0p69 L=4",
          "XR1_2 r1_1 vq2 VGND sky130_fd_pr__res_xhigh_po_0p69 L=4",
          "XRD1 VGND VGND VGND sky130_fd_pr__res_xhigh_po_0p69 L=4",
          "XRD2 VGND VGND VGND sky130_fd_pr__res_xhigh_po_0p69 L=4", ".ends"]
open(os.path.join(CELLS, "bg_res_ref.spice"), "w").write("\n".join(lines) + "\n")
