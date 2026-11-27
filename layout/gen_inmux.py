#!/usr/bin/env python3
"""Chunk 2e — inmux: 4:1 input multiplexer, four transmission gates (full-custom, Magic layers). Version 2 (2026-11-16):
gate pads along the top edge (the enables come straight down from adc_digital's south edge) and the inputs on
straps that leave on the right (from the R3 corridor). v1 (gen_inmux_v1.py) had its gate pads interleaved with
the input straps, which left no room for the top-level vias.

TG k connects vadc to input k (0 vin, 1 vptat, 2 vbg, 3 VGND): NMOS 4/0.15 (gate en_k) + PMOS lvt 8/0.35 (gate en_kb).
Vertical gates (W along y). Four diffusions side by side, each two transistors sharing their vadc strip:
      NMOS A: in0 | en0 | vadc | en1 | in1      NMOS B: in2 | en2 | vadc | en3 | in3      (W = 4)
      PMOS A: in0 | en0b | vadc | en1b | in1    PMOS B: in2 | en2b | vadc | en3b | in3    (W = 8, in the nwell)
The vadc strip is 0.8 um wide so the gate pads (one row above the PMOS) clear each other. Every S/D strip runs
down on li + met1 to one of five met2 straps under the cell (vin, vptat, vbg, VGND, vadc).
p-tap column (VGND) left of the NMOS, n-tap column (VDPWR) right of the PMOS.
Pins: en0..3, en0b..3b (met1 pads, top); vin, vptat, vbg, vadc (met2, right end); VGND, VDPWR (met1 columns).
Usage: python3 layout/gen_inmux.py && python3 layout/check_cell.py inmux
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout

WN, WP = 4.0, 8.0
def segs(L):
    """(start, end) along x of: in_a strip, gate a, vadc strip, gate b, in_b strip."""
    a = 0.29
    return [(0, a), (a, a + L), (a + L, a + L + 0.8), (a + L + 0.8, a + 2 * L + 0.8), (a + 2 * L + 0.8, 2 * a + 2 * L + 0.8)]
NS, PS = segs(0.15), segs(0.35)
XA_N = 0.5
XB_N = XA_N + NS[-1][1] + 0.27
XA_P = XB_N + NS[-1][1] + 0.34 + 0.18 + 0.2
XB_P = XA_P + PS[-1][1] + 0.27
XEND = XB_P + PS[-1][1]
PAD_Y = WP + 0.55
STRAP = {"vin": -0.8, "vptat": -1.6, "vbg": -2.4, "VGND": -3.2, "vadc": -4.0}   # 0.8 pitch: room for via pads
mid = lambda a: (a[0] + a[1]) / 2


def build():
    L = Layout("inmux")
    P = L.paint
    sq = lambda layer, x, y, hx, hy=None: P(layer, x - hx, y - (hx if hy is None else hy), x + hx, y + (hx if hy is None else hy))
    pins = []
    x_right = XEND + 1.2
    for net, y in STRAP.items():                                   # straps (met2)
        P("metal2", -0.25 if net == "VGND" else 0.4, y - 0.15, x_right, y + 0.15)
    for (x0, S, W, ka, kb, dtype, cont, sfx) in ((XA_N, NS, WN, 0, 1, "ndiff", "ndiffc", ""), (XB_N, NS, WN, 2, 3, "ndiff", "ndiffc", ""),
                                                  (XA_P, PS, WP, 0, 1, "pdiff", "pdiffc", "b"), (XB_P, PS, WP, 2, 3, "pdiff", "pdiffc", "b")):
        P(dtype, x0, 0.0, x0 + S[-1][1], W)
        for gi, k in ((1, ka), (3, kb)):                           # gates: vertical poly up to the pad row
            g0, g1 = x0 + S[gi][0], x0 + S[gi][1]
            P("poly", g0, -0.13, g1, PAD_Y)
            if dtype == "pdiff":
                P("pmoslvt", g0, 0.0, g1, W)
            xg = (g0 + g1) / 2
            P("poly", xg - 0.165, PAD_Y - 0.135, xg + 0.165, PAD_Y + 0.135)
            sq("polycont", xg, PAD_Y, 0.085); sq("locali", xg, PAD_Y, 0.165, 0.085); sq("viali", xg, PAD_Y, 0.085)
            sq("metal1", xg, PAD_Y, 0.16, 0.145)
            pins.append((f"en{k}{sfx}", "metal1", (xg - 0.16, PAD_Y - 0.145, xg + 0.16, PAD_Y + 0.145)))
        names = ["vin", "vptat", "vbg", "VGND"]
        for si, net in ((0, names[ka]), (2, "vadc"), (4, names[kb])):   # strips -> li -> met1 -> strap
            xs = x0 + mid(S[si])
            ys = [0.25 + 0.5 * j for j in range(int(W / 0.5))]
            for y in ys:
                sq(cont, xs, y, 0.085)
            P("locali", xs - 0.085, -0.45, xs + 0.085, ys[-1] + 0.165)
            sq("viali", xs, -0.3, 0.085)
            yb = STRAP[net]
            P("metal1", xs - 0.115, yb, xs + 0.115, -0.15)
            sq("metal1", xs, yb, 0.16, 0.19); sq("via1", xs, yb, 0.13); sq("metal2", xs, yb, 0.185, 0.16)
    xt = 0.0                                                       # p-tap column (VGND), tied to the VGND strap
    P("psubdiff", xt - 0.175, 0.0, xt + 0.175, WN)
    for y in [0.25 + 0.5 * j for j in range(int(WN / 0.5))]:
        sq("psubdiffcont", xt, y, 0.085); sq("viali", xt, y, 0.085)
    P("locali", xt - 0.085, 0.08, xt + 0.085, WN - 0.08)
    P("metal1", xt - 0.17, STRAP["VGND"] - 0.19, xt + 0.17, WN)
    sq("via1", xt, STRAP["VGND"], 0.13); sq("metal2", xt, STRAP["VGND"], 0.185, 0.16)
    pins.append(("VGND", "metal1", (xt - 0.17, WN - 0.6, xt + 0.17, WN)))
    xn = XEND + 0.6                                                # n-tap column (VDPWR), inside the nwell
    P("nsubdiff", xn - 0.175, 0.3, xn + 0.175, WP - 0.3)
    for y in [0.55 + 0.5 * j for j in range(int((WP - 0.6) / 0.5))]:
        sq("nsubdiffcont", xn, y, 0.085); sq("viali", xn, y, 0.085)
    P("locali", xn - 0.085, 0.38, xn + 0.085, WP - 0.38)
    P("metal1", xn - 0.17, 0.3, xn + 0.17, WP - 0.3)
    pins.append(("VDPWR", "metal1", (xn - 0.17, WP - 0.9, xn + 0.17, WP - 0.3)))
    # nwell: >= 0.38 um beyond the lvtn implant (lvtn.10). Magic writes lvtn as the pmoslvt channel grown by 0.18 um,
    # and the channels span the whole diffusion height (0 .. WP), so lvtn reaches -0.18 / WP + 0.18 in y
    # (2026-11-27: the well ended 0.38 um from the diffusion, 0.20 um from lvtn; flagged by TT after submission)
    P("nwell", XA_P - 0.38, -0.18 - 0.38, xn + 0.55, WP + 0.18 + 0.38)
    for net in ("vin", "vptat", "vbg", "vadc"):
        y = STRAP[net]
        pins.append((net, "metal2", (x_right - 0.5, y - 0.15, x_right, y + 0.15)))
    for k, (n, layer, b) in enumerate(pins, 1):
        L.pin(n, layer, *b, k)
    return L


if __name__ == "__main__":
    L = build()
    drc, errs, gds = L.run()
    print(f"inmux: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
