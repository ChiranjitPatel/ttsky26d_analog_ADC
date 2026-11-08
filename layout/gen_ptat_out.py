#!/usr/bin/env python3
"""Chunk 1e — ptat_out (scripted): MPP = pfet_01v8 W 16 L 8 (gate vgp) into R3 = 22 x res_xhigh_po_0p69 L 4
(the same unit resistor and source as bandgap_core, sized for matching in Phase 2, 2026-11-08).

    VDPWR --MPP(gate vgp)-- vptat --[R3_1 .. R3_22]-- VGND
Layout: the resistor chain (one array, 2 dummies, guard ring) at the bottom, MPP above it with its own
n-tap guard ring (= VDPWR, also the body). Pins: vgp (met2), vptat (met2), VDPWR (met1), VGND (met1).
Usage: python3 layout/gen_ptat_out.py && python3 layout/check_cell.py ptat_out
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, probe_gencell
from res_chain import add_chain

L = Layout("ptat_out")
ch = add_chain(L, 22, 4.0, 0.0, 0.0, name="R3", w=0.69)
assert not ch["end_top"]
# chain end (strip 22, bottom head) -> VGND: extend the right dummy's bottom met1 stub over it
xs, yb = ch["xs"], ch["yb"]
L.paint("metal1", xs[22] - 0.125, yb - 0.15, xs[23] + 0.125, yb + 0.15)

g = probe_gencell("sky130_fd_pr__pfet_01v8", w=16, l=8, nf=1, guard=1, full_metal=1)
bx0, by0, bx1, by1 = g["bbox"]
px0, py0 = 1.0, ch["bbox"][3] + 1.2
ox, oy = px0 - bx0, py0 - by0
L.gencell("sky130_fd_pr__pfet_01v8", "MPP", ox, oy, w=16, l=8, nf=1, guard=1, full_metal=1)
ring = (bx0 + 0.265 + ox, by0 + 0.265 + oy, bx1 - 0.265 + ox, by1 - 0.265 + oy)
lab = {k: (x + ox, y + oy) for k, (x, y) in g["labels"].items()}
# S -> n-tap ring (VDPWR): li strap; ring -> VDPWR pin: li pad on the right side, mcon, met1
ym = lab["S"][1]
L.paint("locali", lab["S"][0] - 0.1, ym - 0.4, ring[2] + 0.085, ym + 0.4)
L.paint("locali", ring[2] - 0.085, ym - 0.4, ring[2] + 0.7, ym + 0.4)
L.paint("mcon", ring[2] + 0.3, ym - 0.085, ring[2] + 0.47, ym + 0.085)
L.pin("VDPWR", "metal1", ring[2] + 0.2, ym - 0.3, ring[2] + 0.6, ym + 0.3, 1)
# D -> vptat: via1 on the drain strip's met1, met2 down the left side to the chain start (bottom head)
dx, dy = lab["D"]
L.paint("metal1", dx - 0.25, dy - 0.3, dx + 0.25, dy + 0.3)   # the drain strip's met1 is too narrow for via1
L.paint("via1", dx - 0.13, dy - 0.15, dx + 0.13, dy + 0.15)
L.paint("metal2", dx - 0.28, dy - 0.3, dx + 0.28, dy + 0.3)
sx, sy = ch["start"]
yv = ch["ring"][1] - 1.0
xv = ch["ring"][0] - 1.5                     # outside the chain's VGND bar
L.wire("metal2", dx, dy, xv, dy, 0.4)
L.wire("metal2", xv, dy, xv, yv, 0.4)
L.wire("metal2", xv, yv, sx, yv, 0.4)
L.wire("metal2", sx, yv, sx, sy, 0.4)
L.pin("vptat", "metal2", xv - 0.2, yv - 0.2, xv + 0.2, yv + 0.4, 2)
# G -> vgp: via1 on the gate contact's met1, met2 up
gx, gy = lab["G"]
L.paint("metal1", gx - 0.3, gy - 0.25, gx + 0.3, gy + 0.25)
L.paint("via1", gx - 0.15, gy - 0.15, gx + 0.15, gy + 0.15)
L.paint("metal2", gx - 0.3, gy - 0.3, gx + 0.3, gy + 0.3)
L.wire("metal2", gx, gy, gx, ring[3] + 1.2, 0.4)
L.pin("vgp", "metal2", gx - 0.2, ring[3] + 0.6, gx + 0.2, ring[3] + 1.2, 3)
b = ch["vgnd_bar"]
L.pin("VGND", "metal1", b[0], (b[1] + b[3]) / 2 - 0.5, b[2], (b[1] + b[3]) / 2 + 0.5, 4)

drc, errs, gds = L.run()
print(f"ptat_out: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
