#!/usr/bin/env python3
"""Chunk 1g — vref_buf (scripted, layout/mos_rows.py): NMOS-input follower + reservoir cap.

Rows, bottom to top:
  0  NMOS  MCRES x3                            reservoir cap (7 x nfet 10/10, gate = vref, D/S/B = VGND)
  1  NMOS  MCRES x3
  2  NMOS  MCRES | MT | MSW | M1 M2            tail, enable switch (short L: middle row), input pair
  3  PMOS  M3 M4 | MPU                         mirror load, power-down pull-up
Pins: nbias, en, in (left buses), vref (right), VGND (left), VDPWR (right).
Usage: python3 layout/gen_vref_buf.py && python3 layout/check_cell.py vref_buf
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
mos_rows.BUS = 0.6
N, PL, P = "nfet_01v8", "pfet_01v8_lvt", "pfet_01v8"
cap = lambda k: Dev(f"MCRES_{k}", N, 10, 10, D="VGND", G="vref", S="VGND")
c = Cell("vref_buf")
c.add_row([cap(1), cap(2), cap(3)], "VGND")
c.add_row([cap(4), cap(5), cap(6)], "VGND")
# MT (schematic 10 x 2/2 = 10 unit currents) drawn as 2 x 10/2: the same W/L, LVS merges parallel devices
c.add_row([cap(7), Dev("MT_1", N, 10, 2, D="tail_sw", G="nbias", S="VGND"), Dev("MT_2", N, 10, 2, D="tail_sw", G="nbias", S="VGND"),
           Dev("MSW", N, 4, 0.15, rot=270, D="tail", G="en", S="tail_sw"),
           Dev("M1", N, 4, 1, D="dm", G="in", S="tail"), Dev("M2", N, 4, 1, D="vref", G="vref", S="tail")], "VGND")
c.add_row([Dev("M3", PL, 4, 1, D="dm", G="dm", S="VDPWR"), Dev("M4", PL, 4, 1, D="vref", G="dm", S="VDPWR"),
           Dev("MPU", P, 0.42, 1, D="dm", G="en", S="VDPWR")], "VDPWR")
c.build(pins_left=("nbias", "en", "in"), pins_right=("vref",))
drc, errs, gds = c.write()
print(f"vref_buf: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
