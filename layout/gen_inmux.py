#!/usr/bin/env python3
"""Chunk 2e — inmux: 4:1 input multiplexer, four transmission gates (full-custom, Magic layers).

TG k connects vadc to input k (0 vin, 1 vptat, 2 vbg, 3 VGND): NMOS 4/0.15 (gate en_k) + PMOS lvt 8/0.35 (gate enb_k).
Two stacks, each one NMOS diffusion (W = 4) next to one PMOS diffusion (W = 8), gates horizontal:
      in_a | gate a | vadc | gate b | in_b          stack 0: a = 0, b = 1     stack 1: a = 2, b = 3
The NMOS strips are stretched so every strip lines up with its PMOS partner; met2 straps join them across
the gap between the two diffusions. NMOS gate pads on the left, PMOS gate pads on the right.
p-tap row below the NMOS (VGND), n-tap row above the PMOS (VDPWR).
Pins: vin, vptat, vbg (met2 straps, left end), vadc (met2), en0..3 (met1, left), en0b..3b (met1, right),
VGND, VDPWR. Input 3 (VGND) is tied to the VGND rail inside the cell.
Usage: python3 layout/gen_inmux.py && python3 layout/check_cell.py inmux
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout

WN, WP = 4.0, 8.0
XN = 0.9                                  # NMOS diffusion left edge (gate pads at XN - 0.5)
XP = XN + WN + 1.4                        # PMOS diffusion left edge (nwell spacing 0.34 + enclosure 0.18)
# one stack, y relative to its bottom (PMOS L = 0.35, NMOS L = 0.15 centred on the PMOS gates)
P_SEG = [(0.0, 0.29), (0.29, 0.64), (0.64, 0.94), (0.94, 1.29), (1.29, 1.58)]      # in_a, g_a, vadc, g_b, in_b
N_GATES = [(0.39, 0.54), (1.04, 1.19)]
STRIP_Y = [0.145, 0.79, 1.435]            # licon / strap centres (in_a, vadc, in_b)
STACK_DY = 1.85
Y0 = 1.0                                  # bottom of stack 0
mid = lambda a: (a[0] + a[1]) / 2


def build():
    L = Layout("inmux")
    P = L.paint
    sq = lambda layer, x, y, hx, hy=None: P(layer, x - hx, y - (hx if hy is None else hy), x + hx, y + (hx if hy is None else hy))
    W = XP + WP + 0.9
    ytop = Y0 + STACK_DY + 1.58
    # p-tap row (VGND) under the NMOS, n-tap row (VDPWR) above the PMOS
    P("metal1", 0, 0.0, W, 0.48); P("locali", 0, 0.04, W, 0.44); P("psubdiff", 0.25, 0.065, XN + WN + 0.3, 0.415)
    yt = ytop + 0.55
    P("metal1", 0, yt, W, yt + 0.48); P("locali", 0, yt + 0.04, W, yt + 0.44)
    P("nsubdiff", XP - 0.2, yt + 0.065, W - 0.25, yt + 0.415)
    for x in [0.5 + 0.5 * k for k in range(int((XN + WN - 0.45) / 0.5) + 1)]:
        sq("psubdiffcont", x, 0.24, 0.085); sq("viali", x, 0.24, 0.085)
    for x in [XP + 0.05 + 0.5 * k for k in range(int((W - 0.5 - XP - 0.05) / 0.5) + 1)]:
        sq("nsubdiffcont", x, yt + 0.24, 0.085); sq("viali", x, yt + 0.24, 0.085)
    P("nwell", XP - 0.4, Y0 - 0.3, W, yt + 0.6)
    pins = []
    def gate_pad(x, y, pin):
        P("poly", x - 0.165, y - 0.135, x + 0.165, y + 0.135)
        sq("polycont", x, y, 0.085); sq("locali", x, y, 0.085, 0.165); sq("viali", x, y, 0.085)
        sq("metal1", x, y, 0.145, 0.16)
        pins.append((pin, "metal1", (x - 0.145, y - 0.16, x + 0.145, y + 0.16)))
    strap_x = {}
    for s in range(2):
        y0 = Y0 + s * STACK_DY
        ka, kb = 2 * s, 2 * s + 1
        # NMOS
        P("ndiff", XN, y0, XN + WN, y0 + 1.58)
        for (ga, gb), k in zip(N_GATES, (ka, kb)):
            P("poly", XN - 0.5 - 0.165, y0 + ga, XN + WN + 0.13, y0 + gb)
            gate_pad(XN - 0.5, y0 + mid((ga, gb)), f"en{k}")
        # PMOS (lvt)
        P("pdiff", XP, y0, XP + WP, y0 + 1.58)
        for seg, k in ((P_SEG[1], ka), (P_SEG[3], kb)):
            P("poly", XP - 0.13, y0 + seg[0], XP + WP + 0.5 + 0.165, y0 + seg[1])
            P("pmoslvt", XP, y0 + seg[0], XP + WP, y0 + seg[1])
            gate_pad(XP + WP + 0.5, y0 + mid(seg), f"en{k}b")
        # strips: licons + li, mcon + met1 + via1 at the inner ends, met2 strap across
        for j, ys in enumerate(STRIP_Y):
            y = y0 + ys
            for x0, w, cont in ((XN, WN, "ndiffc"), (XP, WP, "pdiffc")):
                cxs = [x0 + 0.25 + 0.5 * i for i in range(int(w / 0.5))]
                for cx in cxs:
                    sq(cont, cx, y, 0.085)
                P("locali", cxs[0] - 0.165, y - 0.085, cxs[-1] + 0.165, y + 0.085)
            xa, xb = XN + WN - 0.25, XP + 0.25            # inner contact columns
            for x in (xa, xb):
                sq("viali", x, y, 0.085); sq("metal1", x, y, 0.19, 0.16)      # encloses via1 (0.06 / 0.03)
                sq("via1", x, y, 0.13); sq("metal2", x, y, 0.185, 0.16)
            net = ("vadc" if j == 1 else ["vin", "vptat", "vbg", "VGND"][ka if j == 0 else kb])
            P("metal2", xa - 0.185, y - 0.16, xb + 0.185, y + 0.16)
            strap_x[(net, s)] = (xa, xb, y)
    # vadc: the two stacks' straps joined by a met1 vertical in the gap between the diffusions
    xj = (XN + WN + XP) / 2
    ya, yb = strap_x[("vadc", 0)][2], strap_x[("vadc", 1)][2]
    for y in (ya, yb):
        P("metal2", strap_x[("vadc", 0)][0], y - 0.16, xj + 0.185, y + 0.16)
        sq("via1", xj, y, 0.13); sq("metal1", xj, y, 0.15, 0.16)
    P("metal1", xj - 0.15, ya, xj + 0.15, yb)
    # inputs leave on met2 to the left edge (vin, vptat, vbg); VGND input: met1 down to the tap row
    xs, xe, y = strap_x[("VGND", 1)]
    for net in ("vin", "vptat", "vbg"):
        xa, xb, y = strap_x[[k for k in strap_x if k[0] == net][0]]
        # the strap runs left under the NMOS gate pads only on met2 (pads are met1)
        P("metal2", 0.1, y - 0.15, xa, y + 0.15)
        pins.append((net, "metal2", (0.1, y - 0.15, 0.6, y + 0.15)))
    # VGND input strap: met1 from its NMOS-side contact down the left of the NMOS?  The NMOS strip li runs
    # the full width; tie it to the tap row through li at the NMOS right end, where nothing else runs.
    xa, xb, y = strap_x[("VGND", 1)]
    # VGND (input 3) is the top strip of stack 1: li down would cross the other strips, so use met2 -> via1 ->
    # met1 in the gap, down to the VGND rail
    xg = xj + 0.445                        # between the vadc join (xj) and the PMOS-side contact pads
    P("metal2", xa - 0.185, y - 0.16, xg + 0.185, y + 0.16)
    sq("via1", xg, y, 0.13); sq("metal1", xg, y, 0.15, 0.16)
    P("metal1", xg - 0.15, 0.0, xg + 0.15, y)
    pins.append(("vadc", "metal2", (strap_x[("vadc", 0)][0] - 0.185, ya - 0.16, strap_x[("vadc", 0)][0] + 0.185, ya + 0.16)))
    pins += [("VGND", "metal1", (0.0, 0.0, 0.5, 0.48)), ("VDPWR", "metal1", (W - 0.5, yt, W, yt + 0.48))]
    for k, (n, layer, b) in enumerate(pins, 1):
        L.pin(n, layer, *b, k)
    return L


if __name__ == "__main__":
    L = build()
    drc, errs, gds = L.run()
    print(f"inmux: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
