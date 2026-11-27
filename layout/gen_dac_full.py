#!/usr/bin/env python3
"""M2 — dac: the capacitor array (gen_cap_dac.draw) and its nine bottom-plate switches (gen_dac_sw.draw) in one cell.

The switch row sits under the array's group buses at a 7.0 um pitch (two array columns), offset so that each
switch's bottom-plate node bp lands exactly in a 1.2 um gap between plate columns (x = 7 k - 0.6, array-local).
bp_k rises from the PMOS drain strip on met3 (crossing the switch row's rails and met2 lines, and the lower
buses) to its own bus (via2). No met3 comes closer than 1.2 um to a bottom plate (the top bus is 1.5 um below
the plates).
Switch inputs for the top level:
  gn_k, gpb_k  met4 landing pads (via stack to the gate pads, jogged on met1 by 1.9 / 0.9 um to the left so the
               two landings of one column and the bp via stay apart); the top level drops onto them from met4
               tracks running under the cell (over vref_buf / vcm_gen, which use no met4)
  smp, smpb    met1 pads at the right end; vadc, vref: met2 lines (pins at the left end)
VGND: the switch row's p-tap rail joins the array's VGND bus at the right end (met3); VDPWR: the n-tap rail.
Usage: python3 layout/gen_dac_full.py && python3 layout/check_cell.py dac
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout
import gen_cap_dac, gen_dac_sw

PITCH, X0S = 7.0, 0.7
OXS = -0.6 - 0.3 - X0S                 # switch row origin x: bp of column 0 at the gap x = -0.6
SW_H = gen_dac_sw.NWELL_Y1             # switch row height (nwell top; 5.69 since the lvtn.10 fix, was 5.6)
X_LEFT = -1.7                          # cell left edge (array-local)


def build():
    L = Layout("dac")
    sq = lambda layer, x, y, hx, hy=None: L.paint(layer, x - hx, y - (hx if hy is None else hy), x + hx, y + (hx if hy is None else hy))
    apins, BUS_Y, _ = gen_cap_dac.draw(L, bus_x0=X_LEFT, bus_x1=gen_cap_dac.CX(gen_cap_dac.N - 1) + 0.6)
    oys = min(BUS_Y.values()) - 0.2 - 0.6 - SW_H          # switch row below the lowest bus (VGND), 0.6 um gap
    spins = gen_dac_sw.draw(L, ox=OXS, oy=oys, pitch=PITCH, x0=X0S)
    buses = {f"bp{i}": f"b{i}" for i in range(8)}; buses["bpt"] = "bpt"
    pins = {}
    # bp -> bus: via1 + via2 at the bp top, met3 up to the bus, via2 down onto it
    for bp, bus in buses.items():
        x, _, _, box = spins[bp]
        yb = box[3]                                   # top of the bp pin box = the PMOS drain contact
        sq("metal1", x, yb, 0.16, 0.19); sq("via1", x, yb, 0.13); sq("metal2", x, yb, 0.22); sq("via2", x, yb, 0.16); sq("metal3", x, yb, 0.25)
        yt = BUS_Y[bus]
        L.paint("metal3", x - 0.15, yb, x + 0.15, yt)
        sq("metal3", x, yt, 0.25); sq("via2", x, yt, 0.16); sq("metal2", x, yt, 0.22)
    # gn / gpb: met1 jog left, then a via stack up to a met4 landing pad (the pin)
    for i in range(8):
        for net, jog in ((f"gn{i}", 1.4), (f"gpb{i}", 0.4)):
            x, y, _, _ = spins[net]
            xl = x - jog
            L.paint("metal1", xl - 0.15, y - 0.16, x, y + 0.16)
            sq("via1", xl, y, 0.13); sq("metal2", xl, y, 0.22, 0.25)
            sq("via2", xl, y, 0.16); sq("metal3", xl, y, 0.3)
            sq("via3", xl, y, 0.2); sq("metal4", xl, y, 0.3)
            pins[net] = ("metal4", (xl - 0.3, y - 0.3, xl + 0.3, y + 0.3))
    # VGND: switch-row p-tap rail -> array VGND bus at the right end (met3 over the n-tap rail; the left end is
    # taken by column 0's gn/gpb landings)
    w_sw = X0S + PITCH * 8 + gen_dac_sw.WP_HI + 1.0
    xg = OXS + w_sw + 0.55
    yr = oys + 0.24
    L.paint("metal1", OXS + w_sw - 0.5, oys, xg + 0.25, oys + 0.48)
    sq("metal1", xg, yr, 0.25, 0.24); sq("via1", xg, yr, 0.13); sq("metal2", xg, yr, 0.22)
    sq("via2", xg, yr, 0.16); sq("metal3", xg, yr, 0.25)
    L.paint("metal3", xg - 0.15, yr, xg + 0.15, BUS_Y["VGND"])
    sq("metal3", xg, BUS_Y["VGND"], 0.25); sq("via2", xg, BUS_Y["VGND"], 0.16); sq("metal2", xg, BUS_Y["VGND"], 0.22)
    L.paint("metal1", X_LEFT, oys, OXS + 0.5, oys + 0.48)              # rail out to the cell edge
    for n in ("smp", "smpb", "vadc", "vref", "VDPWR", "VGND"):
        pins[n] = (spins[n][2], spins[n][3])
    pins["vtop"] = (apins["vtop"][2], apins["vtop"][3])
    for k, (n, (layer, b)) in enumerate(pins.items(), 1):
        L.pin(n, layer, *b, k)
    return L


if __name__ == "__main__":
    L = build()
    drc, errs, gds = L.run()
    print(f"dac: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
