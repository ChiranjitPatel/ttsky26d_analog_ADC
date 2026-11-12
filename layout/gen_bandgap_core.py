#!/usr/bin/env python3
"""Chunk 1d — bandgap_core (scripted, layout/mos_rows.py + the chunk 1c cells).

Rows, bottom to top (OTA as in gen_ota.py, plus the bandgap's own devices):
  0  NMOS  M6 M3 M4 M6 | RZ | MND MIN | MSU3 MSU1 MSD            (OTA loads + startup)
  1  PMOS  D M1 M2 M2 M1 D | M5 M7 | MPD MIP                      (OTA input pair: inp = vb, inn = va)
  2  PMOS  D MPA MPB MPC D | MSU2                                 (current sources, dummies 16/1)
  CC = 4 x MIM 16 x 16 over rows 0 and 1 (as in gen_ota.py)
Band under row 0: pnp_array (layout/cells/pnp_array.gds) and bg_res (layout/cells/bg_res.gds) side by side.
  va   PNP top pin -> met3 in the gap under row 0 -> left bus
  vq3  PNP right pin -> up between the two cells -> over bg_res (met3) -> its top pin (met2)
  vq2, vb, vbg   pins -> met2 drops -> met3 tracks under the band -> vq2 joined, vb / vbg to their buses
  VGND bg_res's ground bar -> PNP array's bottom bar -> VGND rail bus
Pins: pbias, pd, vbg (left buses), vgp (right: the cap strap must not cross the cz top plates), VDPWR (right),
VGND (left).
Usage: python3 layout/gen_bandgap_core.py && python3 layout/check_cell.py bandgap_core
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
from magic_lib import CELLS
mos_rows.BUS = 0.6

N, PL, P, R = "nfet_01v8", "pfet_01v8_lvt", "pfet_01v8", "res_xhigh_po_0p35"
c = Cell("bandgap_core")
m6 = lambda k: Dev(f"M6_{k}", N, 8, 16, rot=270, D="vgp", G="out1", S="VGND")      # OTA out = vgp
c.add_row([m6(1), Dev("M3", N, 4, 16, rot=270, D="d1", G="d1", S="VGND"),
           Dev("M4", N, 4, 16, rot=270, D="out1", G="d1", S="VGND"), m6(2),
           Dev("RZ", R, 0.35, 10.45, series=2, P="out1", M="cz"),
           Dev("MND", N, 0.42, 1, D="out1", G="pd", S="VGND"),
           Dev("MIN", N, 0.42, 1, D="pdb", G="pd", S="VGND"),
           Dev("MSU3", N, 1, 1, D="su", G="vbg", S="VGND"),
           Dev("MSU1", N, 0.42, 4, D="vgp", G="su", S="VGND"),
           Dev("MSD", N, 0.42, 1, D="su", G="pd", S="VGND")], "VGND")
m1 = lambda k: Dev(f"M1_{k}", PL, 16, 8, D="d1", G="va", S="tail")
m2 = lambda k: Dev(f"M2_{k}", PL, 16, 8, D="out1", G="vb", S="tail")
dp = lambda k: Dev(f"MDP{k}", PL, 16, 1, D="VDPWR", G="VDPWR", S="VDPWR")
c.add_row([dp(1), m1(1), m2(1), m2(2), m1(2), dp(2),
           Dev("M5", PL, 4, 2, D="tail", G="pbias", S="VDPWR"), Dev("M7", PL, 8, 2, D="vgp", G="pbias", S="VDPWR"),
           Dev("MPD", P, 0.42, 1, D="vgp", G="pdb", S="VDPWR"), Dev("MIP", P, 0.84, 1, D="pdb", G="pd", S="VDPWR")], "VDPWR")
ds = lambda k: Dev(f"MDS{k}", P, 16, 1, D="VDPWR", G="VDPWR", S="VDPWR")
src = lambda nm, d: Dev(nm, P, 16, 8, D=d, G="vgp", S="VDPWR")
c.add_row([ds(1), src("MPA", "va"), src("MPB", "vb"), src("MPC", "vbg"), ds(2),
           Dev("MSU2", PL, 2, 2, D="su", G="pbias", S="VDPWR")], "VDPWR")

# band geometry (below row 0)
PNP_W, PNP_H, PNP_LL = 28.72, 22.28, (-1.30, -1.30)     # pnp_array bbox size and its lower-left in cell coords
RES_W, RES_H, RES_LL = 29.06, 15.25, (-0.75, -2.50)     # bg_res
BAND_TOP = -4.0
TRK = [BAND_TOP - PNP_H - 1.2 - 0.9 * k for k in range(3)]   # tracks under the band: vq2, vb, vbg
c.build(pins_left=("pbias", "pd", "vbg", "va", "vb", "cz"), pins_right=("vgp",), no_pin=("va", "vb", "cz"),
        bus_ylo=TRK[-1] - 1.0)
L = c.L

# ---- Miller cap (as in gen_ota.py) ----
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
    L.paint("metal3", xa + CW - 0.5, y, xb + 0.5, y + CH)
    L.paint("metal4", xa + 17.6, y + 0.4, xb + 0.8, y + 16.0)
y0, y1 = row_y(0), row_y(1)
L.paint("metal4", xa + 17.6, y0 + 0.4, xb + 0.8, y1 + 16.0)
xcz = xa + CW + GAP / 2
xo = xb + 17.9
L.paint("metal4", xo - 0.24, y0 + 0.1, xo + 0.24, y1 + CH - 0.1)

def stack_to_bus(net, x_from, y):
    xbus = c.bus_x[net]
    L.paint("metal4", min(x_from, xbus) - 0.3, y - 0.3, max(x_from, xbus) + 0.3, y + 0.3)
    L.paint("metal3", xbus - 0.3, y - 0.3, xbus + 0.3, y + 0.3)
    L.paint("via3", xbus - 0.2, y - 0.2, xbus + 0.2, y + 0.2)
    L.paint("metal2", xbus - 0.25, y - 0.25, xbus + 0.25, y + 0.25)
    L.paint("via2", xbus - 0.16, y - 0.16, xbus + 0.16, y + 0.16)

ych = c.rows[0]["y"] - 0.6
L.paint("metal4", xcz - 0.3, ych - 0.3, xcz + 0.3, y0 + 3.0)
stack_to_bus("cz", xcz, ych)
stack_to_bus("vgp", xo, (c.rows[1]["y"] + c.rows[1]["top"]) / 2)     # OTA out (bottom plates) = vgp

# ---- band: pnp_array + bg_res ----
px = c.rows[0]["x0"]                                   # bbox lower-left of pnp_array
py = BAND_TOP - PNP_H
rx = px + PNP_W + 2.0                                  # bbox lower-left of bg_res
ry = BAND_TOP - RES_H
L.place_gds(os.path.join(CELLS, "pnp_array.gds"), "pnp_array", px, py)
L.place_gds(os.path.join(CELLS, "bg_res.gds"), "bg_res", rx, ry)
P = lambda x, y: (px + x - PNP_LL[0], py + y - PNP_LL[1])     # pnp_array pin coords -> cell coords
Q = lambda x, y: (rx + x - RES_LL[0], ry + y - RES_LL[1])     # bg_res pin coords -> cell coords

def landing(x, y):
    L.paint("metal2", x - 0.22, y - 0.22, x + 0.22, y + 0.22)
    L.paint("via2", x - 0.16, y - 0.16, x + 0.16, y + 0.16)
    L.paint("metal3", x - 0.25, y - 0.25, x + 0.25, y + 0.25)

# va: PNP top pin (met3) -> up to y_va -> left on met3 to the va bus
vax, vay = P(9.79, 20.28)
y_va = BAND_TOP + 2.0
L.paint("metal3", vax - 0.3, vay - 0.3, vax + 0.3, y_va + 0.25)
L.paint("metal3", c.bus_x["va"] - 0.25, y_va - 0.25, vax + 0.3, y_va + 0.25)
landing(c.bus_x["va"], y_va)
# vq3: PNP right pin (met3) -> right into the gap -> up above bg_res -> right -> down onto bg_res's vq3 (met2)
q3x, q3y = P(26.72, 9.79)
gx = px + PNP_W + 1.0                                  # middle of the gap between the two cells
t3x, t3y = Q(25.48, 12.6)
y_q3 = BAND_TOP + 0.6
L.paint("metal3", q3x - 0.3, q3y - 0.3, gx + 0.3, q3y + 0.3)
L.paint("metal3", gx - 0.3, q3y - 0.3, gx + 0.3, y_q3 + 0.3)
L.paint("metal3", gx - 0.3, y_q3 - 0.3, t3x + 0.3, y_q3 + 0.3)
L.paint("metal2", t3x - 0.2, t3y - 0.2, t3x + 0.2, y_q3 + 0.2)
landing(t3x, y_q3)
# tracks under the band: vq2 (PNP left pin <-> bg_res vq2), vb and vbg (bg_res -> buses)
def drop(x, y_from, y_trk, from_met3=False):
    if from_met3:
        landing(x, y_from)                              # pin met3 -> met2
    L.paint("metal2", x - 0.2, y_trk - 0.2, x + 0.2, y_from + 0.2)
    landing(x, y_trk)
q2px, q2py = P(-0.7, 9.79)
q2rx, q2ry = Q(19.63, -2.35)
L.paint("metal2", q2px - 0.2, q2py - 0.2, q2px + 0.2, q2py + 0.2)
drop(q2px, q2py, TRK[0])
drop(q2rx, q2ry, TRK[0], from_met3=True)
L.paint("metal3", q2px - 0.25, TRK[0] - 0.25, q2rx + 0.25, TRK[0] + 0.25)
vbx, vby = Q(7.93, -2.35)
drop(vbx, vby, TRK[1], from_met3=True)
L.paint("metal3", c.bus_x["vb"] - 0.25, TRK[1] - 0.25, vbx + 0.25, TRK[1] + 0.25)
landing(c.bus_x["vb"], TRK[1])
vgx, vgy = Q(2.08, -2.35)
drop(vgx, vgy, TRK[2])
L.paint("metal3", c.bus_x["vbg"] - 0.25, TRK[2] - 0.25, vgx + 0.25, TRK[2] + 0.25)
landing(c.bus_x["vbg"], TRK[2])
# VGND: bg_res ground bar (left side, met1) down to the PNP bottom bar level, and that bar to the rail bus
gbx, gby = Q(-0.6, 3.7)
pbx, pby = P(0.5, -0.9)
L.paint("metal1", gbx - 0.15, pby - 0.3, gbx + 0.15, gby + 0.3)
L.paint("metal1", c.bus_x["VGND"] - 0.2, pby - 0.3, gbx + 0.15, pby + 0.3)

drc, errs, gds = c.write()
print(f"bandgap_core: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
