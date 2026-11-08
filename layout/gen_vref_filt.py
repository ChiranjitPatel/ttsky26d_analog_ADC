#!/usr/bin/env python3
"""Chunk 1f — vref_filt (scripted): RF = 9 x res_xhigh_po_0p35 L = 20 um in series (~1.04 MOhm) and
MCF = nfet_01v8 W = 10 L = 10 as a gate capacitor (~3.9 pF) from vbg_f to VGND.

    vbg --[RF_1 .. RF_9]-- vbg_f --||-- VGND        (MCF gate = vbg_f; D, S, B = VGND)
Layout: the resistor chain (one array, 2 dummies, guard ring) on the left, MCF on the right; vbg_f runs
on met2 from the chain end to the MCF gate. Pins: vbg (met2, bottom), vbg_f (met2, top), VGND (met1).
Usage: python3 layout/gen_vref_filt.py && python3 layout/check_cell.py vref_filt
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, probe_gencell
from res_chain import add_chain

L = Layout("vref_filt")
ch = add_chain(L, 9, 20.0, 0.0, 0.0, name="RF")
N_CAP = 5                                                  # MCF: 5 x (W 10, L 10) in parallel = schematic mult = 5
g = probe_gencell("sky130_fd_pr__nfet_01v8", w=10, l=10, nf=1, guard=1, full_metal=1)
bx0, by0, bx1, by1 = g["bbox"]
cw, chh = bx1 - bx0, by1 - by0
cx0 = ch["bbox"][2] + 1.5
sites = [(cx0 + c * (cw + 0.6), r * (chh + 0.6)) for r in (0, 1) for c in range(3)][:N_CAP]
gates = []
xbar = ch["ring"][2] + 0.45                                # chain's right VGND bar (met1)
for i, (sx, sy) in enumerate(sites):
    ox, oy = sx - bx0, sy - by0
    L.gencell("sky130_fd_pr__nfet_01v8", f"MCF_{i+1}", ox, oy, w=10, l=10, nf=1, guard=1, full_metal=1)
    ring = (bx0 + 0.265 + ox, by0 + 0.265 + oy, bx1 - 0.265 + ox, by1 - 0.265 + oy)
    lab = {k: (x + ox, y + oy) for k, (x, y) in g["labels"].items()}
    ym = lab["D"][1]
    # D and S strips -> own guard ring (li straps across the diffusion-to-tap gap)
    L.paint("locali", ring[0] - 0.085, ym - 0.4, lab["D"][0] + 0.1, ym + 0.4)
    L.paint("locali", lab["S"][0] - 0.1, ym - 0.4, ring[2] + 0.085, ym + 0.4)
    # ring -> VGND: li pad on the bottom ring, mcon, met1 bus along the row (below the ring)
    xm = (ring[0] + ring[2]) / 2
    L.paint("locali", xm - 0.4, ring[1] - 0.45, xm + 0.4, ring[1] + 0.085)
    L.paint("mcon", xm - 0.085, ring[1] - 0.3, xm + 0.085, ring[1] - 0.13)
    L.paint("metal1", xm - 0.3, ring[1] - 0.4, xm + 0.3, ring[1] - 0.05)
    gx, gy = lab["G"]
    L.paint("metal1", gx - 0.3, gy - 0.25, gx + 0.3, gy + 0.25)
    L.paint("via1", gx - 0.15, gy - 0.15, gx + 0.15, gy + 0.15)
    L.paint("metal2", gx - 0.3, gy - 0.3, gx + 0.3, gy + 0.3)
    gates.append((gx, gy))
    if i % 3 == 0:                                         # VGND met1 bus for this row, from the chain bar
        row_y = ring[1] - 0.225
        row_x1 = sites[min(i + 2, N_CAP - 1)][0] + cw
        L.paint("metal1", xbar, row_y - 0.175, row_x1, row_y + 0.175)
# rows joined to the chain bar: the chain bar spans the chain height; extend it to the top row's bus
L.paint("metal1", xbar, ch["vgnd_bar"][1], xbar + 0.3, sites[-1][1] + 0.5)
# vbg_f: met2 gate bus over each row, joined on the right, and to the chain end (top head)
assert ch["end_top"]
ex, ey = ch["end"]
xr = max(gx for gx, _ in gates) + 1.5
for r in (0, 1):
    row = [p for i, p in enumerate(gates) if i // 3 == r]
    L.wire("metal2", row[0][0], row[0][1], xr, row[0][1], 0.4)
L.wire("metal2", xr, gates[0][1], xr, gates[3][1], 0.4)
yr = gates[0][1]
L.wire("metal2", ex, ey, ex, ey + 1.0, 0.4)
L.wire("metal2", ex, ey + 1.0, gates[0][0] - 1.0, ey + 1.0, 0.4)
L.wire("metal2", gates[0][0] - 1.0, ey + 1.0, gates[0][0] - 1.0, yr, 0.4)
L.wire("metal2", gates[0][0] - 1.0, yr, gates[0][0], yr, 0.4)
L.pin("vbg_f", "metal2", xr - 0.2, gates[3][1], xr + 0.2, gates[3][1] + 0.6, 2)
# vbg: chain start (bottom head) -> met2 down
sx, sy = ch["start"]
L.wire("metal2", sx, sy, sx, ch["ring"][1] - 1.5, 0.4)
L.pin("vbg", "metal2", sx - 0.2, ch["ring"][1] - 1.5, sx + 0.2, ch["ring"][1] - 0.9, 1)
b = ch["vgnd_bar"]
L.pin("VGND", "metal1", b[0], (b[1] + b[3]) / 2 - 0.5, b[2], (b[1] + b[3]) / 2 + 0.5, 3)

drc, errs, gds = L.run()
print(f"vref_filt: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
