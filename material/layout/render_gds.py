#!/usr/bin/env python3
"""Render a GDS top cell to a PNG (white background) for review.
Usage: render_gds.py in.gds out.png [title] [--labels all|power]
Draws wells, diffusion, poly, the poly-resistor marker, li, met1-met4 and vias; writes pin labels
(all labels by default; 'power' = only VDPWR/VGND, for the full tile)."""
import sys
import klayout.db as db
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=") for a in sys.argv[1:] if a.startswith("--") and "=" in a)
LAB = opts.get("labels", "all")
# (layer, datatype): (name, face, edge, alpha), drawn in this order
LAYERS = {(64, 20): ("nwell", "#fff3c4", "#c9a500", 0.6), (65, 20): ("diff", "#b6e3b6", "#2e8b2e", 0.6),
          (66, 20): ("poly", "#f4b6b6", "#c0392b", 0.6), (69, 216): ("poly res (xhigh)", "#7f7f7f", "#000000", 0.25),
          (67, 20): ("li1", "#c9b6e3", "#7d5ba6", 0.35), (68, 20): ("met1", "#1f77b4", "#1f77b4", 0.35),
          (68, 44): ("via1", "black", "black", 0.9), (69, 20): ("met2", "#9467bd", "#9467bd", 0.35),
          (69, 44): ("via2", "#444444", "#444444", 0.9), (70, 20): ("met3", "#2ca02c", "#2ca02c", 0.45),
          (70, 44): ("via3", "black", "black", 1.0), (71, 20): ("met4", "#ff7f0e", "#ff7f0e", 0.45),
          (71, 16): ("met4 pin", "#d62728", "#d62728", 0.9), (235, 4): ("prBoundary", "none", "black", 1.0)}
ly = db.Layout(); ly.read(args[0]); top = ly.top_cell()
b = top.bbox(); w, h = b.width() * ly.dbu, b.height() * ly.dbu
scale = 9.5 / max(w, h)
fig, ax = plt.subplots(figsize=(max(4, w * scale + 1.5), max(3.5, h * scale + 1.2))); fig.patch.set_facecolor("white")
seen = set()
for (l, d), (name, fc, ec, a) in LAYERS.items():
    li = ly.find_layer(l, d)
    if li is None:
        continue
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_box() or s.is_polygon() or s.is_path():
            p = s.polygon.transformed(it.trans())
            pts = [(pt.x * ly.dbu, pt.y * ly.dbu) for pt in p.each_point_hull()]
            ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, alpha=a, lw=0.5, label=None if name in seen else name))
            seen.add(name)
        it.next()
# labels on the metal / li label purposes (datatype 5 = label, 16 = pin)
done = set()
for l in (67, 68, 69, 70, 71):
    for d in (5, 16):
        li = ly.find_layer(l, d)
        if li is None:
            continue
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            # top-cell labels only (device-internal labels like Emitter/R1_0 would clutter the picture)
            if s.is_text() and it.cell_index() == top.cell_index():
                tx = s.text.transformed(it.trans())
                key = (tx.string, round(tx.x * ly.dbu), round(tx.y * ly.dbu))
                if key not in done and (LAB == "all" or tx.string in ("VDPWR", "VGND")):
                    ax.text(tx.x * ly.dbu, tx.y * ly.dbu, tx.string, fontsize=8, ha="center", va="center",
                            rotation=0 if LAB == "all" else 90, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
                    done.add(key)
            it.next()
m = 0.06 * max(w, h)
ax.set_xlim(b.left * ly.dbu - m, b.right * ly.dbu + m); ax.set_ylim(b.bottom * ly.dbu - m, b.top * ly.dbu + m)
ax.set_aspect("equal"); ax.set_xlabel("x [µm]"); ax.set_ylabel("y [µm]")
ax.set_title(args[2] if len(args) > 2 else top.name, fontsize=10)
ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0))
ax.grid(alpha=0.2); fig.tight_layout(); fig.savefig(args[1], dpi=130, facecolor="white")
print("wrote", args[1])
