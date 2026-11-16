#!/usr/bin/env python3
"""Chunk 2b — dac_sw_row: the nine DAC bottom-plate switches in one compact full-custom cell (Magic layers).

Each switch is one vertical column (5 um pitch), bits 7 .. 0 then the termination t (left to right):
  NMOS stack, one diffusion W = 1:     VGND | gate gn_k (MSG 1/0.15) | bp_k | gate smp (MSN 1/0.15) | vadc
  PMOS lvt stack, one diffusion:       vadc | gate smpb (MSP 2/0.35, W = 2) | bp_k | gate gpb_k (MSR 4/0.35, W = 4) | vref
Gates are horizontal poly. smp and smpb are continuous poly lines through all nine columns (contacted at the
right end; a 50 um poly line with ~10 fF of gate load settles in ~0.1 ns). gn_k / gpb_k have a contact pad at the
left of their column. A p-tap row (VGND) at the bottom and an n-tap row (VDPWR) at the top bias the
substrate and the nwell.
Wiring: bp_k  NMOS drain strip -> met1 vertical -> PMOS drain strip (crosses the vadc strips on li).
        vadc  NMOS top strip and PMOS bottom strip joined on li; mcon/via1 to a met2 line in the n/p gap.
        vref  PMOS top strip -> met1 -> via1 -> met2 line above the PMOS row.
        VGND  NMOS bottom strip -> li -> tap row.
Termination column: gn = smpb (met1 from its gn pad up to an extra smpb contact), gpb = VDPWR (met1 up to the rail).
Pins (for the top level): VGND, VDPWR (met1 rails), vadc, vref (met2 lines), smp, smpb (met1 pads at the right
end), gn0..7, gpb0..7 (met1 gate pads), bp0..7, bpt (met1, on the bp vertical).
Usage: python3 layout/gen_dac_sw.py && python3 layout/check_cell.py dac_sw_row
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout

PITCH, X0 = 5.05, 1.6           # 5.05: the next gpb pad clears the previous gate end-cap by 0.21 (poly.2)
COLS = [str(i) for i in range(7, -1, -1)] + ["t"]
# y levels (um)
RAIL_N = (0.0, 0.48)                    # VGND met1 rail
NDIFF = (0.70, 1.88)
N_S0, N_GN, N_D, N_SMP, N_S1 = (0.70, 0.99), (0.99, 1.14), (1.14, 1.44), (1.44, 1.59), (1.59, 1.88)
NWELL_Y0 = 2.22
P_VA, P_SMPB, P_BP, P_GPB, P_VR = (2.40, 2.69), (2.69, 3.04), (3.04, 3.44), (3.44, 3.79), (3.79, 4.08)
P_STEP = 3.12                           # PMOS diffusion: W = 2 below, W = 4 above (inside the bp strip)
VADC_Y, VREF_Y = 2.10, 4.50             # met2 lines
RAIL_P = (4.95, 5.43)                   # VDPWR met1 rail
NWELL_Y1 = 5.60
WN, WP_LO, WP_HI = 1.0, 2.0, 4.0
mid = lambda a: (a[0] + a[1]) / 2


def draw(L, ox=0.0, oy=0.0, pitch=None, x0=None, pins_out=None, width=None):
    """Paint the switch row into Layout L at offset (ox, oy). pitch / x0 override PITCH / X0 (the combined dac
    cell uses a 7.0 um pitch so each bp lands in a gap of the capacitor array). Returns {name: (x, y, layer)}
    for every pin (absolute), and paints/labels nothing as a port unless pins_out is None (standalone cell)."""
    PITCH_, X0_ = (pitch or PITCH), (X0 if x0 is None else x0)
    def P(layer, a, b, c, d):
        L.paint(layer, a + ox, b + oy, c + ox, d + oy)
    sq = lambda layer, x, y, hx, hy=None: P(layer, x - hx, y - (hx if hy is None else hy), x + hx, y + (hx if hy is None else hy))
    xs = [X0_ + PITCH_ * k for k in range(len(COLS))]        # left diffusion edge per column
    W = width or (xs[-1] + WP_HI + 1.0)                      # cell width (the right-end pads need 1.0)
    # rails + taps
    P("metal1", 0, RAIL_N[0], W, RAIL_N[1]); P("locali", 0, 0.04, W, 0.44); P("psubdiff", 0.1, 0.065, W - 0.1, 0.415)
    P("metal1", 0, RAIL_P[0], W, RAIL_P[1]); P("locali", 0, 4.99, W, 5.39); P("nsubdiff", 0.25, 5.02, W - 0.25, 5.37)
    for x in [0.5 + 0.5 * k for k in range(int((W - 1.0) / 0.5) + 1)]:      # >= 0.12 inside the tap ends (licon.7)
        sq("psubdiffcont", x, 0.24, 0.085); sq("viali", x, 0.24, 0.085)
        sq("nsubdiffcont", x, 5.195, 0.085); sq("viali", x, 5.195, 0.085)
    P("nwell", 0, NWELL_Y0, W, NWELL_Y1)
    # global poly lines smp (NMOS upper gate) and smpb (PMOS lower gate), contacted at the left end
    xl = xs[-1] + WP_HI + 0.55                               # smp / smpb contacts at the right end
    P("poly", xs[0] - 0.13, N_SMP[0], xl + 0.165, N_SMP[1])
    P("poly", xs[0] - 0.13, P_SMPB[0], xl + 0.165, P_SMPB[1])
    pins = []
    def gate_pad(x, y, pin=None):
        """poly pad + polycont + li + mcon + met1 pad at (x, y)."""
        P("poly", x - 0.165, y - 0.135, x + 0.165, y + 0.135)        # 0.08 past the contact in x (licon.8a)
        sq("polycont", x, y, 0.085); sq("locali", x, y, 0.085, 0.165); sq("viali", x, y, 0.085)
        sq("metal1", x, y, 0.145, 0.16)
        if pin:
            pins.append((pin, "metal1", (x - 0.145, y - 0.16, x + 0.145, y + 0.16)))
    gate_pad(xl, mid(N_SMP), "smp")
    gate_pad(xl, mid(P_SMPB), "smpb")
    for k, (c, x) in enumerate(zip(COLS, xs)):
        term = c == "t"
        # --- NMOS: one diffusion VGND | gn | bp | smp | vadc
        P("ndiff", x, NDIFF[0], x + WN, NDIFF[1])
        P("poly", x - 0.5 - 0.135, N_GN[0], x + WN + 0.13, N_GN[1])          # gn gate, pad on the left
        gate_pad(x - 0.5, mid(N_GN), None if term else f"gn{c}")
        for (y0, y1) in (N_S0, N_D, N_S1):
            yc = mid((y0, y1))
            for cx in (x + 0.25, x + 0.75):
                sq("ndiffc", cx, yc, 0.085)
            P("locali", x + 0.25 - 0.165, yc - 0.085, x + 0.75 + 0.165, yc + 0.085)      # 0.08 past the contacts (li.5)
        P("locali", x + 0.415, 0.44, x + 0.585, mid(N_S0))                     # S0 -> VGND tap row
        # --- PMOS lvt: vadc | smpb | bp | gpb | vref; W = 2 up to P_STEP, W = 4 above
        P("pdiff", x, P_VA[0], x + WP_LO, P_STEP); P("pdiff", x, P_STEP, x + WP_HI, P_VR[1])
        P("poly", x - 0.5 - 0.135, P_GPB[0], x + WP_HI + 0.13, P_GPB[1])      # gpb gate, pad on the left
        gate_pad(x - 0.5, mid(P_GPB), None if term else f"gpb{c}")
        for (y0, y1), w in ((P_VA, WP_LO), ((P_BP[0], P_STEP + 0.2), WP_LO), (P_VR, WP_HI)):
            yc = mid(P_VA) if (y0, y1) == P_VA else (mid(P_VR) if (y0, y1) == P_VR else P_BP[0] + 0.055 + 0.085 + 0.01)
            cxs = [x + 0.25 + 0.5 * j for j in range(int(w / 0.5))]
            for cx in cxs:
                sq("pdiffc", cx, yc, 0.085)
            P("locali", cxs[0] - 0.165, yc - 0.085, cxs[-1] + 0.165, yc + 0.085)
        # lvt channels (poly over pdiff paints a regular pmos first)
        P("pmoslvt", x, P_SMPB[0], x + WP_LO, P_SMPB[1]); P("pmoslvt", x, P_GPB[0], x + WP_HI, P_GPB[1])
        # --- bp: NMOS drain strip -> met1 vertical -> PMOS drain strip
        xb = x + 0.3
        ybn, ybp = mid(N_D), P_BP[0] + 0.15
        sq("viali", xb, ybn, 0.085); sq("viali", xb, ybp, 0.085)
        P("metal1", xb - 0.115, ybn - 0.145, xb + 0.115, ybp + 0.145)
        pins.append(("bpt" if term else f"bp{c}", "metal1", (xb - 0.115, ybp - 0.4, xb + 0.115, ybp)))
        # --- vadc: NMOS top strip + PMOS bottom strip on li, mcon/via1 to the met2 line
        xr = x + 0.8
        P("locali", xr - 0.085, mid(N_S1), xr + 0.085, mid(P_VA))
        sq("viali", xr, VADC_Y, 0.085); sq("metal1", xr, VADC_Y, 0.15, 0.185)
        sq("via1", xr, VADC_Y, 0.13); sq("metal2", xr, VADC_Y, 0.185, 0.215)
        # --- vref: PMOS top strip -> met1 -> via1 -> met2 line
        xv = x + 2.5
        sq("viali", xv, mid(P_VR), 0.085)
        P("metal1", xv - 0.15, mid(P_VR) - 0.145, xv + 0.15, VREF_Y + 0.185)
        sq("via1", xv, VREF_Y, 0.13); sq("metal2", xv, VREF_Y, 0.185, 0.215)
        if term:
            # gn_t = smpb: met1 from the gn pad up to an extra smpb contact (the smpb poly passes here);
            # gpb_t = VDPWR: met1 from the gpb pad up to the rail
            xg = x - 0.5
            gate_pad(xg, mid(P_SMPB))
            P("metal1", xg - 0.145, mid(N_GN), xg + 0.145, mid(P_SMPB))
            P("metal1", xg - 0.145, mid(P_GPB), xg + 0.145, RAIL_P[0] + 0.1)
    P("metal2", 0.2, VADC_Y - 0.15, W - 0.2, VADC_Y + 0.15)
    P("metal2", 0.2, VREF_Y - 0.15, W - 0.2, VREF_Y + 0.15)
    pins += [("vadc", "metal2", (0.2, VADC_Y - 0.15, 0.7, VADC_Y + 0.15)),
             ("vref", "metal2", (0.2, VREF_Y - 0.15, 0.7, VREF_Y + 0.15)),
             ("VGND", "metal1", (0.0, RAIL_N[0], 0.5, RAIL_N[1])),
             ("VDPWR", "metal1", (0.0, RAIL_P[0], 0.5, RAIL_P[1]))]
    out = {n: ((b[0] + b[2]) / 2 + ox, (b[1] + b[3]) / 2 + oy, layer, tuple(v + (ox if i % 2 == 0 else oy) for i, v in enumerate(b))) for n, layer, b in pins}
    return out


def build():
    L = Layout("dac_sw_row")
    pins = draw(L)
    for k, (n, (x, y, layer, b)) in enumerate(pins.items(), 1):
        L.pin(n, layer, *b, k)
    return L


if __name__ == "__main__":
    L = build()
    drc, errs, gds = L.run()
    print(f"dac_sw_row: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
