#!/usr/bin/env python3
"""Chunk 2c — comparator (scripted, layout/mos_rows.py): preamp + PMOS-input StrongARM + output inverters + MTOP.

Rows (bottom to top). Short-L devices sit in the two middle rows, where mos_rows takes their gate from the
lower channel and their D/S from the upper one (no stub clash next to a 0.15 um gate):
  0 NMOS            MAL1 MAL2 (preamp diode loads 0.5/1) | MTOP (2/0.15, rotated)
  1 NMOS (short L)  MR1 MR3 MION M5 M6 MINN MR4 MR2             reset 0.42/0.15, latch 1/0.15, inverters
  2 PMOS (short L)  MIOP MA1 M1 MT M2 MA2 MINP                  preamp pair lvt 4/0.5, latch pair lvt 4/0.5
  3 PMOS            M3 | MAT x4 (lvt 2/2 units, the bias_gen MP2 unit: mirror rule) | M4    (M3/M4 2/0.15, rotated)
Rotated short-L devices (both D and S on signal nets) go in the outer rows, where all their stubs leave on
the same side; the unrotated short-L ones go in the middle rows (gate down, D/S up).
Matched pairs (MA1/MA2, M1/M2, M3/M4, M5/M6, MAL1/MAL2, MR1/MR2, MR3/MR4, inverters) are mirror-symmetric
about the row centre. MTOP (top-plate switch vtop -> vcm) sits at the row end next to the inp/inn buses.
Pins: pbias, clkb, smpt, opb (left); onb, inn (= vcm), inp (= vtop) (right; VDPWR bus between onb and inn); VGND, VDPWR.
Usage: python3 layout/gen_comparator.py && python3 layout/check_cell.py comparator
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
mos_rows.BUS = 0.6
mos_rows.TRACK = 0.8          # met3 track 0.5 + 0.3 spacing (rule minimum)
N, P, PL = "nfet_01v8", "pfet_01v8", "pfet_01v8_lvt"
c = Cell("comparator")
X0 = (7.5, 3.4, 4.0)          # rows 0-2 centred on row 3 (row 2 +0.1: met2 stub spacing) (widths 10.0, 18.2, 17.3 against 25.0): equal track lengths
                              # to the mirrored side buses
c.add_row([Dev("MAL1", N, 0.5, 1, D="pan", G="pan", S="VGND"), Dev("MAL2", N, 0.5, 1, D="pap", G="pap", S="VGND"),
           Dev("MTOP", N, 2, 0.15, rot=270, D="inp", G="smpt", S="inn")], "VGND", x0=X0[0])
c.add_row([Dev("MR1", N, 0.42, 0.15, D="xp", G="clkb", S="VGND"), Dev("MR3", N, 0.42, 0.15, D="op", G="clkb", S="VGND"),
           Dev("MION", N, 0.42, 0.15, D="opb", G="op", S="VGND"), Dev("M5", N, 1, 0.15, D="op", G="on", S="VGND"),
           Dev("M6", N, 1, 0.15, D="on", G="op", S="VGND"), Dev("MINN", N, 0.42, 0.15, D="onb", G="on", S="VGND"),
           Dev("MR4", N, 0.42, 0.15, D="on", G="clkb", S="VGND"), Dev("MR2", N, 0.42, 0.15, D="xn", G="clkb", S="VGND")], "VGND", x0=X0[1])
c.add_row([Dev("MIOP", P, 0.84, 0.15, D="opb", G="op", S="VDPWR"),
           Dev("MA1", PL, 4, 0.5, D="pan", G="inp", S="pts"), Dev("M2", PL, 4, 0.5, D="xp", G="pan", S="ts"),
           Dev("MT", P, 4, 0.15, D="ts", G="clkb", S="VDPWR"),
           Dev("M1", PL, 4, 0.5, D="xn", G="pap", S="ts"), Dev("MA2", PL, 4, 0.5, D="pap", G="inn", S="pts"),
           Dev("MINP", P, 0.84, 0.15, D="onb", G="on", S="VDPWR")], "VDPWR", x0=X0[2])
c.add_row([Dev("M3", P, 2, 0.15, rot=270, D="op", G="on", S="xp")]
          + [Dev(f"MAT_{k}", PL, 2, 2, D="pts", G="pbias", S="VDPWR") for k in range(1, 5)]
          + [Dev("M4", P, 2, 0.15, rot=270, D="on", G="op", S="xn")], "VDPWR")
# Symmetry (the extracted comparator had a -64 mV offset; -178 mV in the whole tile): the side buses mirror the
# matched pairs - op/pan/xp/opb on the left, on/pap/xn/onb on the right, each group shielded by a rail bus from the
# other buses (left: the digital inputs; right: inp/inn). By default every multi-channel net went to the left, so
# xn's and pap's tracks crossed the cell (xn 41 fF vs xp 30 fF). The unpaired nets that enter from one side
# (clkb, pbias, smpt), and inp/inn (both buses on the right), get mirror-image track extensions, so they couple
# equally to both halves.
AXIS = 25.04 / 2              # row 3's centre; rows 0-2 are centred on it
c.build(pins_left=("pbias", "clkb", "smpt", "opb"), pins_right=("inp", "inn", "onb"), pack=True,
        bus_order={"left": ["op", "pan", "xp", "opb", "VGND", "clkb", "pbias", "smpt"],
                   "right": ["on", "pap", "xn", "onb", "VDPWR", "inn", "inp"]},
        mirror=(AXIS, ("clkb", "pbias", "smpt", "ts", "pts", "inp", "inn")))
print("buses", {k: round(v, 2) for k, v in c.bus_x.items()})
drc, errs, gds = c.write()
for i, r in enumerate(c.rows):
    print(f"row {i}: x {r['x0']:.2f} .. {r['x1']:.2f}  y {r['y']:.2f} .. {r['top']:.2f}")
print(f"comparator: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
