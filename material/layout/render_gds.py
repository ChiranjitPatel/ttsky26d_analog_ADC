#!/usr/bin/env python3
"""Render a GDS top cell to a PNG (white background) for review. Usage: render_gds.py in.gds out.png [title]"""
import sys
import klayout.db as db
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
LAYERS = {(235, 4): ("prBoundary", "none", "black", 1.0), (68, 20): ("met1", "#1f77b4", "#1f77b4", 0.35),
          (69, 20): ("met2", "#9467bd", "#9467bd", 0.35), (70, 20): ("met3", "#2ca02c", "#2ca02c", 0.45),
          (71, 20): ("met4", "#ff7f0e", "#ff7f0e", 0.45), (71, 16): ("met4 pin", "#d62728", "#d62728", 0.9),
          (70, 44): ("via3", "black", "black", 1.0)}
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
fig, ax = plt.subplots(figsize=(7, 9.8)); fig.patch.set_facecolor("white")
seen = set()
for (l, d), (name, fc, ec, a) in LAYERS.items():
    li = ly.find_layer(l, d)
    if li is None: continue
    for sh in top.begin_shapes_rec(li).each() if False else []: pass
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_box() or s.is_polygon() or s.is_path():
            p = s.polygon.transformed(it.trans())
            pts = [(pt.x * ly.dbu, pt.y * ly.dbu) for pt in p.each_point_hull()]
            ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, alpha=a, lw=0.6, label=None if name in seen else name))
            seen.add(name)
        it.next()
    for t in []: pass
# labels
li = ly.find_layer(71, 5)
if li is not None:
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_text():
            tx = s.text.transformed(it.trans())
            if tx.string in ("VDPWR", "VGND"):
                ax.text(tx.x * ly.dbu, tx.y * ly.dbu, tx.string, fontsize=8, rotation=90, ha="center", va="center")
        it.next()
b = top.bbox(); ax.set_xlim(b.left * ly.dbu - 3, b.right * ly.dbu + 3); ax.set_ylim(b.bottom * ly.dbu - 3, b.top * ly.dbu + 3)
ax.set_aspect("equal"); ax.set_xlabel("x [µm]"); ax.set_ylabel("y [µm]")
ax.set_title(sys.argv[3] if len(sys.argv) > 3 else top.name, fontsize=10); ax.legend(fontsize=7, loc="center")
ax.grid(alpha=0.2); fig.tight_layout(); fig.savefig(sys.argv[2], dpi=110, facecolor="white")
print("wrote", sys.argv[2])
