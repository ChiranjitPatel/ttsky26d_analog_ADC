#!/usr/bin/env python3
"""Chunk 1h — vref_sel (scripted, layout/mos_rows.py): enable logic + the ua[1] transmission gate.

Rows, bottom to top:
  0  NMOS  MN1A MN1B MN2A MN2B MN3             logic (L = 1)
  1  NMOS  MTGN                                TG nfet 10/0.15 (short L: middle row, gate stub down)
  2  PMOS  MTGP                                TG pfet_lvt 20/0.35
  3  PMOS  MP1A MP1B MP2A MP2B MP3             logic (L = 1); MP1A/MP1B and MP2A/MP2B in series
Pins: ref_sel, vref_oe, bg_pd, en_buf (left), vref, pad (right), VGND (left), VDPWR (right).
Usage: python3 layout/gen_vref_sel.py && python3 layout/check_cell.py vref_sel
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mos_rows
from mos_rows import Cell, Dev
mos_rows.BUS = 0.6
N, P, PL = "nfet_01v8", "pfet_01v8", "pfet_01v8_lvt"
c = Cell("vref_sel")
c.add_row([Dev("MN1A", N, 0.42, 1, D="en_buf", G="ref_sel", S="VGND"), Dev("MN1B", N, 0.42, 1, D="en_buf", G="bg_pd", S="VGND"),
           Dev("MN2A", N, 0.42, 1, D="en_pad_b", G="ref_sel", S="VGND"), Dev("MN2B", N, 0.42, 1, D="en_pad_b", G="vref_oe", S="VGND"),
           Dev("MN3", N, 0.42, 1, D="en_pad", G="en_pad_b", S="VGND")], "VGND")
c.add_row([Dev("MTGN", N, 10, 0.15, rot=270, D="pad", G="en_pad", S="vref")], "VGND")
c.add_row([Dev("MTGP", PL, 20, 0.35, rot=270, D="pad", G="en_pad_b", S="vref")], "VDPWR")
# series stacks: S of the left device = D of the right one (direct jumper)
c.add_row([Dev("MP1B", P, 1.68, 1, D="en_buf", G="bg_pd", S="nb1"), Dev("MP1A", P, 1.68, 1, D="nb1", G="ref_sel", S="VDPWR"),
           Dev("MP2B", P, 1.68, 1, D="en_pad_b", G="vref_oe", S="nb2"), Dev("MP2A", P, 1.68, 1, D="nb2", G="ref_sel", S="VDPWR"),
           Dev("MP3", P, 0.84, 1, D="en_pad", G="en_pad_b", S="VDPWR")], "VDPWR")
c.build(pins_left=("ref_sel", "vref_oe", "bg_pd", "en_buf"), pins_right=("vref", "pad"))
drc, errs, gds = c.write()
print(f"vref_sel: Magic DRC {drc}; {gds}", *errs, sep="\n  ")
