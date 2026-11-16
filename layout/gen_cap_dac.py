#!/usr/bin/env python3
"""Chunk 2a — cap_array: the 8-bit binary MIM DAC array (scripted, Magic).

256 active units (cap_mim_m3_1, capm 2 x 1.65 um, ~8.0 fF) in a 16 x 16 common-centroid pattern, plus a dummy
column on each side (16 x 18 grid, 32 dummies). No dummy rows: the array has to fit 62 um of height (2026-11-16).
  b7 128, b6 64, b5 32, b4 16, b3 8, b2 4, b1 2, b0 1, bpt 1 (termination; its switch has b tied low).
Pattern: one 8 x 8 quadrant pattern mirrored into the four quadrants, so every group's centroid is the array
centre (b0 / bpt: half a unit off). In the quadrant, the units are taken in bit-reversed Z order: each group
gets a regular sub-lattice (b7 = every other column, b6 = every other row of the rest, ...). The four
centre units are b1, b1 (diagonal), b0 and bpt.

Geometry (pitch 3.5 um in x and y):
  bottom plate  met3 2.3 x 2.285 (capm + 0.15; +0.485 tab at the top for the via2, which must stay 0.1 um
                outside the capm), 1.2 um between plates (MR_capm.SP.2)
  top plate     mimcapcontact + met4 pad on every unit; active rows joined by met4 strips, the rows by three
                met4 spines (columns 1, 8, 16); the column-8 spine leaves the array at the top = vtop.
                Dummy top plates: met4 strips on the dummy columns -> VGND.
  bottom-plate routing: via2 in the tab -> met2 stub -> via1 -> met1 track (vertical, one per group per
                column, under the plates) -> down to ten horizontal met2 buses below the array.
                Tracks run under the bottom plates, so the plates shield them from vtop; they see vtop only
                where they cross a 1.2 um gap.
Pins: vtop (met4, top), b7 .. b0, bpt, VGND (met2 buses, right end).
Usage: python3 layout/gen_cap_dac.py && python3 layout/check_cell.py cap_array
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout

PX, PY = 3.5, 3.5
PW, PH = 2.3, 2.285                     # bottom plate (met3)
CM = (0.15, 0.15, 2.15, 1.80)           # capm 2 x 1.65
CC = (0.35, 0.35, 1.95, 1.60)           # mimcapcontact
TP = (0.34, 0.34, 1.96, 1.61)           # met4 pad over the contact
V2 = (0.36, 2.06)                       # bottom-plate via2 (in the tab, 0.1 above the capm)
SLOTS = (0.15, 0.65, 1.15, 1.65, 2.15)   # met1 track x offsets: all under the plate (shielded from vtop; a
                                          # 7-slot version with tracks in the gaps gave 0.45 LSB DNL)
NR, N = 16, 18                          # rows, columns (columns 0 and 17: dummies)
GROUPS = ["b7", "b6", "b5", "b4", "b3", "b2", "b1", "b0", "bpt", "VGND"]
BUS_Y = {g: -1.0 - 0.7 * k for k, g in enumerate(GROUPS)}
CX = lambda c: c * PX + 1.15            # unit centre
CY = lambda r: r * PY + 0.975


def pattern():
    """(i, j) in the 16 x 16 active array -> group."""
    def morton(a, b):
        return sum((((a >> k) & 1) << (2 * k + 1)) | (((b >> k) & 1) << (2 * k)) for k in range(3))
    brev6 = lambda x: int(f"{x:06b}"[::-1], 2)
    cells = sorted(((a, b) for a in range(8) for b in range(8)), key=lambda c: brev6(morton(*c)))
    q, k = {}, 1
    for g, n in (("b2", 1), ("b3", 2), ("b4", 4), ("b5", 8), ("b6", 16), ("b7", 32)):
        for c in cells[k:k + n]:
            q[c] = g
        k += n
    G = {}
    for i in range(16):
        for j in range(16):
            a, b = (7 - i if i < 8 else i - 8), (7 - j if j < 8 else j - 8)
            G[(i, j)] = {(7, 7): "b1", (8, 8): "b1", (7, 8): "b0", (8, 7): "bpt"}[(i, j)] if (a, b) == (0, 0) else q[(a, b)]
    return G


def site_group(r, c, G):
    if c in (0, N - 1):
        return "VGND"
    return G[(r, c - 1)]


def build():
    G = pattern()
    L = Layout("cap_array")
    sq = lambda layer, x, y, h: L.paint(layer, x - h, y - h, x + h, y + h)
    tracks = {}                                         # (col, group) -> (x, ymax)
    for c in range(N):
        groups = sorted({site_group(r, c, G) for r in range(NR)} - {None}, key=GROUPS.index)
        assert len(groups) <= len(SLOTS), (c, groups)
        # spread the used slots over the column
        idx = [round(k * (len(SLOTS) - 1) / max(1, len(groups) - 1)) for k in range(len(groups))] if len(groups) > 1 else [0]
        for g, s in zip(groups, idx):
            tracks[(c, g)] = [c * PX + SLOTS[s], -1e9]
    for r in range(NR):
        for c in range(N):
            g = site_group(r, c, G)
            if g is None:
                continue
            x0, y0 = c * PX, r * PY
            L.paint("metal3", x0, y0, x0 + PW, y0 + PH)
            L.paint("mimcap", x0 + CM[0], y0 + CM[1], x0 + CM[2], y0 + CM[3])
            L.paint("mimcapcontact", x0 + CC[0], y0 + CC[1], x0 + CC[2], y0 + CC[3])
            L.paint("metal4", x0 + TP[0], y0 + TP[1], x0 + TP[2], y0 + TP[3])
            vx, vy = x0 + V2[0], y0 + V2[1]
            sq("via2", vx, vy, 0.16); sq("metal2", vx, vy, 0.25)
            tx = tracks[(c, g)][0]
            L.paint("metal2", min(vx, tx) - 0.15, vy - 0.15, max(vx, tx) + 0.15, vy + 0.15)
            sq("via1", tx, vy, 0.15); sq("metal2", tx, vy, 0.25); sq("metal1", tx, vy, 0.25)
            tracks[(c, g)][1] = max(tracks[(c, g)][1], vy)
    # tracks down to the buses
    xmin, xmax = 1e9, -1e9
    for (c, g), (tx, ytop) in tracks.items():
        yb = BUS_Y[g]
        L.paint("metal1", tx - 0.1, yb, tx + 0.1, ytop)
        sq("via1", tx, yb, 0.15); sq("metal1", tx, yb, 0.25); sq("metal2", tx, yb, 0.25)
        xmin, xmax = min(xmin, tx), max(xmax, tx)
    bx0, bx1 = xmin - 0.25, xmax + 1.6          # pins at the right end, clear of the VGND via stack at CX(17)
    for g, y in BUS_Y.items():
        L.paint("metal2", bx0, y - 0.2, bx1, y + 0.2)
    # top plates: active rows + three spines; vtop out at the top of the column-8 spine
    for r in range(NR):
        L.paint("metal4", CX(1) - 0.25, CY(r) - 0.25, CX(N - 2) + 0.25, CY(r) + 0.25)
    ytop_out = (NR - 1) * PY + PH + 1.0
    for c in (1, 8, N - 2):
        L.paint("metal4", CX(c) - 0.25, CY(0) - 0.25, CX(c) + 0.25, (ytop_out if c == 8 else CY(NR - 1) + 0.25))
    L.pin("vtop", "metal4", CX(8) - 0.25, ytop_out - 0.5, CX(8) + 0.25, ytop_out, 1)
    # dummy top plates: one met4 strip per dummy column -> VGND bus (met4 -> via3 -> met3 -> via2 -> met2)
    w = 0.25
    yg = BUS_Y["VGND"]
    for c in (0, N - 1):
        L.paint("metal4", CX(c) - w, yg - 0.3, CX(c) + w, CY(NR - 1) + w)
        sq("via3", CX(c), yg, 0.2); sq("metal3", CX(c), yg, 0.3); sq("via2", CX(c), yg, 0.16); sq("metal2", CX(c), yg, 0.25)
    for k, g in enumerate(GROUPS):
        y = BUS_Y[g]
        L.pin(g, "metal2", bx1 - 0.5, y - 0.2, bx1, y + 0.2, k + 2)
    return L


if __name__ == "__main__":
    L = build()
    drc, errs, gds = L.run()
    print(f"cap_array: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
