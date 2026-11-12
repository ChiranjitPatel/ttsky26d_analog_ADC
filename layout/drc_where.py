#!/usr/bin/env python3
"""Debug helper: map Magic DRC error boxes (sim/out/layout/<cell>/drc.txt, 5 nm units) to the device
instances of the cell (from the GDS instance bounding boxes). Usage: python3 layout/drc_where.py <cell>"""
import collections, os, re, sys
import klayout.db as db
cell = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
l = db.Layout(); l.read(f"{ROOT}/layout/cells/{cell}.gds"); t = l.top_cell()
insts = [(i.cell.name, i.bbox()) for i in t.each_inst()]
names = {}
for inst in t.each_inst():
    names[inst.bbox().to_s()] = inst.cell.name
txt = open(f"{ROOT}/sim/out/layout/{cell}/drc.txt").read()
# re-run Magic listing with all boxes, not just 5 per rule
rule = None; out = collections.Counter()
for line in txt.splitlines():
    m = re.match(r"(\S.*): (\d+)$", line)
    if m: rule = m.group(1); continue
    m = re.match(r"\s+(-?\d+) (-?\d+) (-?\d+) (-?\d+)", line)
    if m and rule:
        x, y = (int(m.group(1)) + int(m.group(3))) / 2 * 0.005, (int(m.group(2)) + int(m.group(4))) / 2 * 0.005
        p = db.Point(int(x / l.dbu), int(y / l.dbu))
        hit = [n for n, b in insts if b.contains(p)]
        out[(rule[:40], hit[0] if hit else f"channel ({x:.1f},{y:.1f})")] += 1
for (r, w), n in sorted(out.items()): print(f"{n:3d}  {r:42s} {w}")
