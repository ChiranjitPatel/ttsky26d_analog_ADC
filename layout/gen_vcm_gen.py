#!/usr/bin/env python3
"""Chunk 2d — vcm_gen (scripted, layout/mos_rows.py).

Narrow (<= 18.5 um) for the bottom-right strip of floorplan v4; MTOP moved into the comparator (2026-11-16).
  row 0   NMOS  MCV_1 | MD 4/1 (diode)          (MCV: 8/8 gate caps on vcm)
  row 1   NMOS  MCV_2
  row 2-5 PMOS  MB x10 (3 + 3 + 3 + 1; 2/2 units, the same unit as the bias_gen reference MP2: mirror rule, CLAUDE.md 6)
Pins: pbias (left), vcm (right), VGND, VDPWR.
Usage: python3 layout/gen_vcm_gen.py && python3 layout/check_cell.py vcm_gen
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
mos_rows.BUS = 0.6
N, PL = "nfet_01v8", "pfet_01v8_lvt"
c = Cell("vcm_gen")
c.add_row([Dev("MCV_1", N, 8, 8, D="VGND", G="vcm", S="VGND"), Dev("MD", N, 4, 1, D="vcm", G="vcm", S="VGND")], "VGND")
c.add_row([Dev("MCV_2", N, 8, 8, D="VGND", G="vcm", S="VGND")], "VGND")
for ks in ((1, 2, 3), (4, 5, 6), (7, 8, 9), (10,)):
    c.add_row([Dev(f"MB_{k}", PL, 2, 2, D="vcm", G="pbias", S="VDPWR") for k in ks], "VDPWR")
c.build(pins_left=("pbias",), pins_right=("vcm",), pack=True)
drc, errs, gds = c.write()
print(f"vcm_gen: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
