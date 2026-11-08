"""Serpentine chain of res_xhigh_po_0p35 unit strips in one PDK array (common guard ring), with one dummy
strip at each end (both heads and the body on VGND). Geometry comes from probe_gencell, so any unit
length works. Used by gen_ptat_out.py and gen_vref_filt.py.

add_chain(L, n, l_um, start, end, x0=0, y0=0) adds the array with its lower-left guard-ring corner near
(x0, y0) and returns a dict with the pin positions:
  start: bottom head of the first unit (met2 pad), end: the last unit's free head (met2 pad),
  vgnd: met1 bar on the left (ties the dummies and the guard ring)
The drawn length passed to the generator is l_um + 0.16 (it includes the contact overlap; it then
extracts as exactly l_um).
"""
from magic_lib import probe_gencell


def add_chain(L, n, l_um, x0=0.0, y0=0.0, name="R"):
    g = probe_gencell("sky130_fd_pr__res_xhigh_po_0p35", w=0.35, l=l_um + 0.16, nx=n + 2, guard=1)
    bx0, by0, bx1, by1 = g["bbox"]
    ox, oy = x0 - bx0, y0 - by0                    # shift so the bbox starts at (x0, y0)
    ring = (bx0 + 0.265 + ox, by0 + 0.265 + oy, bx1 - 0.265 + ox, by1 - 0.265 + oy)   # guard-ring centre lines
    xs = [g["labels"][f"R1_{i}"][0] + ox for i in range(n + 2)]
    yt = g["labels"]["R1_0"][1] + oy - 0.31        # inside the top head's met1
    yb = g["labels"]["R2_0"][1] + oy + 0.26        # inside the bottom head's met1
    # the generator draws relative to the box corner exactly as in the probe (corner at 0, 0)
    L.gencell("sky130_fd_pr__res_xhigh_po_0p35", name, ox, oy, w=0.35, l=l_um + 0.16, nx=n + 2, guard=1)

    def pad(i, top, hi="metal2"):
        x, y = xs[i], (yt if top else yb)
        L.paint("metal1", x - 0.25, y - 0.25, x + 0.25, y + 0.25)
        L.paint("via1", x - 0.15, y - 0.15, x + 0.15, y + 0.15)
        L.paint("metal2", x - 0.28, y - 0.28, x + 0.28, y + 0.28)
        return x, y

    # serpentine over the active strips 1 .. n: link k joins strip k+1 and k+2, on top for even k
    for k in range(n - 1):
        a, b = 1 + k, 2 + k
        y = yt if k % 2 == 0 else yb
        L.paint("metal1", xs[a] - 0.125, y - 0.15, xs[b] + 0.125, y + 0.15)
    start = pad(1, False)                          # link 0 is on top -> the chain starts at the bottom
    end_top = (n - 2) % 2 == 1                     # the end is opposite the last link (link n-2)
    end = pad(n, end_top)
    # dummies + guard ring -> VGND
    ym = (ring[1] + ring[3]) / 2
    bars = []
    for i, (xr0, xr1, xb0, xb1) in ((0, (ring[0] - 0.75, ring[0] + 0.085, ring[0] - 0.75, ring[0] - 0.45)),
                                     (n + 1, (ring[2] - 0.085, ring[2] + 0.75, ring[2] + 0.45, ring[2] + 0.75))):
        L.paint("locali", xr0, ym - 0.3, xr1, ym + 0.3)
        xm = (xb0 + xb1) / 2
        L.paint("mcon", xm - 0.085, ym - 0.085, xm + 0.085, ym + 0.085)
        L.paint("metal1", xb0, yb - 0.15, xb1, yt + 0.15)
        for y in (yt, yb):
            L.paint("metal1", min(xb0, xs[i] - 0.125), y - 0.15, max(xb1, xs[i] + 0.125), y + 0.15)
        bars.append((xb0, yb - 0.15, xb1, yt + 0.15))
    return {"start": start, "end": end, "end_top": end_top, "vgnd_bar": bars[0],
            "ring": ring, "xs": xs, "yt": yt, "yb": yb, "bbox": (x0, y0, x0 + bx1 - bx0, y0 + by1 - by0)}
