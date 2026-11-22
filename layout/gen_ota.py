#!/usr/bin/env python3
"""Chunk 1b — ota (scripted, layout/mos_rows.py). Brief: docs/specs/layout_briefs/ota.md.

Rows, bottom to top (2026-11-12: two rows, for a 70 um wide bandgap column):
  0  NMOS  M6 M3 M4 M6 | RZ | MND MIN     loads 4/16 rotated (gate length vertical); M6 = 2 x 8/16
  1  PMOS  D M1 M2 M2 M1 D | M5 M5 M7 M7 M7 M7 | MPD MIP   input pair halves 16/8 interdigitated
                                                            (common centroid), dummies 16/1
                                               flank the M3/M4 pair (they act as its dummies)
  1  PMOS  D M1 M2 D | M5 M7 M7 MPD             input pair halves 16/8, common centroid over rows 1 and 2,
  2  PMOS  D M2 M1 D | M5 M7 M7 MIP             dummies 16/1 (same W, short L)
CC = 4 x MIM 16 x 16 (no met3 under them is used): two over row 0 (left one mirrored), one each over rows 1
and 2 stacked above the right one. Top plates (cz) on a vertical met4 bar, bottom-plate strips (out) on a
vertical met4 bar at the right edge; the two row-0 bottom plates are bridged in met3.
Pins (side buses, top end): inp, inn, pd, pbias, cz (left); out (right); VGND (left), VDPWR (right).
Usage: python3 layout/gen_ota.py && python3 layout/check_cell.py ota
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
mos_rows.BUS = 0.6

N, PL, P, R = "nfet_01v8", "pfet_01v8_lvt", "pfet_01v8", "res_xhigh_po_0p35"
c = Cell("ota")
# M6 (schematic 4 x 4/16) drawn as 2 x 8/16: the same total W, netgen merges parallel devices
m6 = lambda k: Dev(f"M6_{k}", N, 8, 16, rot=270, D="out", G="out1", S="VGND")
c.add_row([m6(1), Dev("M3", N, 4, 16, rot=270, D="d1", G="d1", S="VGND"),
           Dev("M4", N, 4, 16, rot=270, D="out1", G="d1", S="VGND"), m6(2),
           Dev("RZ", R, 0.35, 10.45, series=2, P="out1", M="cz"),
           Dev("MND", N, 0.42, 1, D="out1", G="pd", S="VGND"),
           Dev("MIN", N, 0.42, 1, D="pdb", G="pd", S="VGND")], "VGND")
m1 = lambda k: Dev(f"M1_{k}", PL, 16, 8, D="d1", G="inn", S="tail")
m2 = lambda k: Dev(f"M2_{k}", PL, 16, 8, D="out1", G="inp", S="tail")
dp = lambda k: Dev(f"MDP{k}", PL, 16, 1, D="VDPWR", G="VDPWR", S="VDPWR")
m5 = lambda k: Dev(f"M5_{k}", PL, 2, 2, D="tail", G="pbias", S="VDPWR")
m7 = lambda k: Dev(f"M7_{k}", PL, 2, 2, D="out", G="pbias", S="VDPWR")
# M5 (schematic 2 x 2/2) as one 4/2, M7 (4 x 2/2) as one 8/2: same current density, LVS merges units
c.add_row([dp(1), m1(1), m2(1), m2(2), m1(2), dp(2),
           Dev("M5", PL, 4, 2, D="tail", G="pbias", S="VDPWR"), Dev("M7", PL, 8, 2, D="out", G="pbias", S="VDPWR"),
           Dev("MPD", P, 0.42, 1, D="out", G="pdb", S="VDPWR"), Dev("MIP", P, 0.84, 1, D="pdb", G="pd", S="VDPWR")], "VDPWR")
c.build(pins_left=("inp", "inn", "pd", "pbias", "cz"), pins_right=("out",), no_pin=("cz",))

# ---- Miller cap: 4 x MIM 16 x 16, a (mirrored, normal) pair over each row ----
L = c.L
CW, CH, GAP = 18.16, 16.4, 1.0
def row_y(ri):
    r = c.rows[ri]
    return r["y"] + ((r["top"] - r["y"]) - CH) / 2
xa = c.rows[0]["x0"] + 0.5
xb = xa + CW + GAP
for ri in (0, 1):
    y = row_y(ri)
    L.gencell("sky130_fd_pr__cap_mim_m3_1", f"CC_{ri}a", xa, y, flip=True, w=16, l=16, nx=1, ny=1)
    L.gencell("sky130_fd_pr__cap_mim_m3_1", f"CC_{ri}b", xb, y, w=16, l=16, nx=1, ny=1)
    L.paint("metal3", xa + CW - 0.5, y, xb + 0.5, y + CH)                    # bottom plates (out)
    L.paint("metal4", xa + 17.6, y + 0.4, xb + 0.8, y + 16.0)               # top plates (cz), full plate height
y0, y1 = row_y(0), row_y(1)
xcz = xa + CW + GAP / 2                                                       # cz bar between the caps
L.paint("metal4", xa + 17.6, y0 + 0.4, xb + 0.8, y1 + 16.0)    # as wide as the bridges (no plate corners near its edge)
xo = xb + 17.9                                                                # out strips (right caps)
L.paint("metal4", xo - 0.24, y0 + 0.1, xo + 0.24, y1 + CH - 0.1)

def stack_to_bus(net, x_from, y):
    """met4 from x_from to the net's met2 side bus at height y, then via3 + via2 down onto the bus."""
    xbus = c.bus_x[net]
    L.paint("metal4", min(x_from, xbus) - 0.3, y - 0.3, max(x_from, xbus) + 0.3, y + 0.3)
    L.paint("metal3", xbus - 0.3, y - 0.3, xbus + 0.3, y + 0.3)
    L.paint("via3", xbus - 0.2, y - 0.2, xbus + 0.2, y + 0.2)
    L.paint("metal2", xbus - 0.25, y - 0.25, xbus + 0.25, y + 0.25)
    L.paint("via2", xbus - 0.16, y - 0.16, xbus + 0.16, y + 0.16)

# cz leaves the cap bar on met4 through the channel (met4 over the met3 tracks) to the left bus, at a height
# where the bus has no met3 track: just below row 0
ych = c.rows[0]["y"] - 0.6
L.paint("metal4", xcz - 0.3, ych - 0.3, xcz + 0.3, y0 + 3.0)
stack_to_bus("cz", xcz, ych)
stack_to_bus("out", xo, (c.rows[1]["y"] + c.rows[1]["top"]) / 2)

drc, errs, gds = c.write()
print(f"ota: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
