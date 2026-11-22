#!/usr/bin/env python3
"""Chunk 1c — bandgap PNP array (scripted): Q1 x1, Q2 x8, Q3 x1 + 2 dummies, sky130_fd_pr__pnp_05v5_W3p40L3p40.

Arrangement (column 0 left, row 0 bottom; pitch 6.44 um = the PDK device step):
    row 2:  Q2  Q2  Q2  D
    row 1:  Q2  Q1  Q2  Q3        Q1 : Q2 = 1 : 8 common centroid (Q1 in the middle of the 3 x 3)
    row 0:  Q2  Q2  Q2  D         Q3 (single, at the end of R2) and the dummies in a 4th column
All bases and collectors are VGND: the collector rings of neighbouring devices overlap and merge; each
base ring gets an li strap to its collector ring. Emitters:
    vq2  met2 ring through the eight Q2 emitters, pin on the left (met2)
    va   Q1: via stack to met3, out of the top (met3)
    vq3  Q3: via stack to met3, out of the right edge (met3)
    D    emitters tied to VGND on met2, down to the VGND met1 bar under the array
VGND: li pad under row 0 (merged with the collector rings), mcon to a met1 bar, pin on met1.
Writes layout/cells/pnp_array.gds; LVS reference layout/cells/pnp_array_ref.spice.
Usage: python3 layout/gen_pnp_array.py && python3 layout/check_cell.py pnp_array --netlist layout/cells/pnp_array_ref.spice
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, CELLS

P = 6.44                  # device pitch (um), PDK xstep/ystep
C = 3.35                  # emitter centre inside a device cell (cell is 6.70 x 6.70)
GRID = [["Q2", "Q2", "Q2", "D"],   # row 0
        ["Q2", "Q1", "Q2", "Q3"],  # row 1
        ["Q2", "Q2", "Q2", "D"]]   # row 2
W = len(GRID[0]) * P + 0.26        # array extent (um)
H = len(GRID) * P + 0.26

L = Layout("pnp_array")
k = {}
for r, row in enumerate(GRID):
    for c, dev in enumerate(row):
        k[dev] = k.get(dev, 0) + 1
        name = f"{dev}_{k[dev]}" if dev in ("Q2", "D") else dev
        x, y = c * P, r * P
        L.gencell("sky130_fd_pr__pnp_05v5_W3p40L3p40", name, x, y, nx=1, ny=1)
        # base ring -> collector ring (both VGND), li strap below the emitter
        L.paint("locali", x + 3.0, y + 0.46, x + 3.7, y + 1.305)

cx = lambda c: c * P + C
cy = lambda r: r * P + C

# vq2: met2 ring through the eight Q2 emitters
for r, row in enumerate(GRID):
    for c, dev in enumerate(row):
        if dev == "Q2":
            L.via(cx(c), cy(r), "metal1", "metal2", size=0.6, pad=1.0)
L.wire("metal2", cx(0), cy(0), cx(2), cy(0), 0.6)
L.wire("metal2", cx(0), cy(2), cx(2), cy(2), 0.6)
L.wire("metal2", cx(0), cy(0), cx(0), cy(2), 0.6)
L.wire("metal2", cx(2), cy(0), cx(2), cy(2), 0.6)
L.wire("metal2", -1.0, cy(1), cx(0), cy(1), 0.6)
L.pin("vq2", "metal2", -1.0, cy(1) - 0.3, -0.4, cy(1) + 0.3, 1)

# va: Q1 up to met3 and out of the top
L.via(cx(1), cy(1), "metal1", "metal3", size=0.6, pad=1.0)
L.wire("metal3", cx(1), cy(1), cx(1), H + 1.0, 0.8)
L.pin("va", "metal3", cx(1) - 0.4, H + 0.4, cx(1) + 0.4, H + 1.0, 2)

# vq3: Q3 up to met3 and out of the right edge
L.via(cx(3), cy(1), "metal1", "metal3", size=0.6, pad=1.0)
L.wire("metal3", cx(3), cy(1), W + 1.0, cy(1), 0.8)
L.pin("vq3", "metal3", W + 0.4, cy(1) - 0.4, W + 1.0, cy(1) + 0.4, 3)

# VGND: li pad under row 0 (overlaps the row-0 collector rings), mcon to a met1 bar
L.paint("locali", 0.13, -1.3, W - 0.13, 0.29)
L.paint("metal1", 0.0, -1.3, W, -0.5)
xm = 0.6
while xm < W - 0.6:
    L.paint("mcon", xm, -1.05, xm + 0.17, -0.88); xm += 1.0
L.pin("VGND", "metal1", 0.0, -1.3, 1.0, -0.5, 4)

# dummies: emitter -> met2 -> down the right part of column 3 -> via1 onto the VGND bar
xd = 3 * P + 5.6
for r in (0, 2):
    L.via(cx(3), cy(r), "metal1", "metal2", size=0.6, pad=1.0)
    L.wire("metal2", cx(3), cy(r), xd, cy(r), 0.6)
L.wire("metal2", xd, cy(2), xd, -0.9, 0.6)
L.via(xd, -0.9, "metal1", "metal2", size=0.5, pad=0.8)

drc, errs, gds = L.run()
print(f"pnp_array: Magic DRC {drc}; {gds}", *errs, sep="\n  ")

ref = os.path.join(CELLS, "pnp_array_ref.spice")
open(ref, "w").write("""* LVS reference for layout/cells/pnp_array.gds (from bandgap_core: Q1, Q2 m=8, Q3, + 2 dummies)
* PNP pins: collector base emitter
.subckt pnp_array vq2 va vq3 VGND
XQ1 VGND VGND va sky130_fd_pr__pnp_05v5_W3p40L3p40 m=1
XQ2 VGND VGND vq2 sky130_fd_pr__pnp_05v5_W3p40L3p40 m=8
XQ3 VGND VGND vq3 sky130_fd_pr__pnp_05v5_W3p40L3p40 m=1
XQD VGND VGND VGND sky130_fd_pr__pnp_05v5_W3p40L3p40 m=2
.ends
""")
