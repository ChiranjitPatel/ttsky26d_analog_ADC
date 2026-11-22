#!/usr/bin/env python3
"""Chunk 1a — bias_gen (scripted, layout/mos_cell.py). Brief: docs/specs/layout_briefs/bias_gen.md.

NMOS row (VGND ring):  MDN1 MN2 MN2 MN1 MN2 MN2 MDN2 | R1 (2 strips + 2 dummies) | MS3 MS1 MND1 MND2 MIN
    MN1 : MN2 = 1 : 4 common centroid (D B B A B B D), same orientation, dummies at both ends
PMOS row (VDPWR ring): MDP1 MP1 MP2 MDP2 | MS2B MS2A MPD2 | MPD1 MIP
    MP1/MP2 matched pair with dummies; the MS2 series chain (and its end 'sup' into MPD2) is joined by
    direct met1 jumpers across the shared ring lines.
Pins: nbias, pbias (met3, right), pd (met3, left), VDPWR (PMOS ring met1), VGND (NMOS ring met1).
Usage: python3 layout/gen_bias_gen.py && python3 layout/check_cell.py bias_gen
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mos_cell import Cell, Dev

N, P, PL, R = "nfet_01v8", "pfet_01v8", "pfet_01v8_lvt", "res_xhigh_po_0p35"

def nrow():
    mn2 = lambda i: Dev(f"MN2_{i}", N, 2, 2, D="pbias", G="nbias", S="nr")
    return [Dev("MDN1", N, 2, 2, D="VGND", G="VGND", S="VGND"), mn2(1), mn2(2),
            Dev("MN1", N, 2, 2, D="nbias", G="nbias", S="VGND"), mn2(3), mn2(4),
            Dev("MDN2", N, 2, 2, D="VGND", G="VGND", S="VGND"),
            Dev("R1", R, 0.35, 5.45, series=2, P="nr", M="VGND"),     # R1A + R1B (+ 2 dummy strips)
            Dev("MS3", N, 4, 2, D="su", G="nbias", S="VGND"),
            Dev("MS1", N, 0.42, 1, D="pbias", G="su", S="VGND"),
            Dev("MND1", N, 0.42, 1, D="nbias", G="pd", S="VGND"),
            Dev("MND2", N, 0.42, 1, D="su", G="pd", S="VGND"),
            Dev("MIN", N, 0.42, 1, D="pdb", G="pd", S="VGND")]

def prow():
    chain = ["sup", "ms2_1", "su"]
    ms2 = [Dev(f"MS2{'AB'[i]}", P, 0.42, 10, D=chain[i + 1], G="VGND", S=chain[i]) for i in range(2)][::-1]
    return ([Dev("MDP1", PL, 2, 2, D="VDPWR", G="VDPWR", S="VDPWR"),
             Dev("MP1", PL, 2, 2, D="nbias", G="pbias", S="VDPWR"),
             Dev("MP2", PL, 2, 2, D="pbias", G="pbias", S="VDPWR"),
             Dev("MDP2", PL, 2, 2, D="VDPWR", G="VDPWR", S="VDPWR")]
            + ms2 +
            [Dev("MPD2", P, 0.42, 1, D="sup", G="pd", S="VDPWR"),
             Dev("MPD1", P, 0.42, 1, D="pbias", G="pdb", S="VDPWR"),
             Dev("MIP", P, 0.84, 1, D="pdb", G="pd", S="VDPWR")])

def build(y_hi, dx):
    c = Cell("bias_gen")
    c.row("lo", nrow(), "VGND", 0.0, 0.0)
    c.row("hi", prow(), "VDPWR", dx, y_hi)
    c.connect()
    return c

# pass 1: shift the PMOS row until the channel tracks can be ordered (stubs of different nets that
# line up in x would otherwise overlap), and count the tracks
for k in range(60):
    dx = 0.1 * k
    probe = build(100.0, dx)
    try:
        probe.channel_order(); break
    except RuntimeError:
        continue
else:
    raise SystemExit("no PMOS-row offset gives a routable channel")
print(f"PMOS row offset {dx:.1f} um, {len(probe.channel_order())} channel tracks")
y_hi = probe.rows["lo"]["top"] + 1.2 + probe.channel_height()
c = build(y_hi, dx)
c.route(pins_left=("pd",), pins_right=("nbias", "pbias"))
c.rail_pin("lo", "VGND"); c.rail_pin("hi", "VDPWR")
drc, errs, gds = c.write()
print(f"bias_gen: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
