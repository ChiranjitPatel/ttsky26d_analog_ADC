"""Scripted analog cells with any number of device rows (Magic, sky130A). Generalizes mos_cell.py.

Model
-----
* rows[0] is the bottom row. Between rows i and i+1 there is routing channel i. Each row has a rail
  (VGND for NMOS rows, VDPWR for PMOS rows); devices in a row have their own guard rings (0.8 um apart)
  joined by a met1 rail bar along the row's bottom ring line. Rows containing pfets get one n-well.
* Devices: PDK generator cells, optionally rotated (rot=90/270: the gate length runs vertically, so long-L
  devices stack in a narrow row). Ring met1 is generated on the two ring lines that end up horizontal.
* Terminals on the row's rail: li strap to the nearest ring line. Series jumpers: right-hand S of a
  device and left-hand D of its neighbour on a net used nowhere else (unrotated devices only).
* Every other terminal: via1 + met2 stub to its net's met3 track in the adjacent channel (bottom row ->
  channel above, top row -> channel below, middle rows -> the nearer channel). Track order per channel
  from a vertical-constraint graph (as in mos_cell.py).
* Side buses: a net used in more than one channel, or with a pin, gets a vertical met2 bus at the left
  or right side of the cell; its tracks run to the bus (via2). Rails: each row's rail bar runs to a
  vertical met1 rail bus (VGND on the left, VDPWR on the right); a rail used in a channel (e.g. a PMOS gate
  on VGND) joins its rail bus through its track (via2 + via1).
* Pins: on the side buses (met2 for signals, met1 for rails), at the top end.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, probe_gencell

INSET = 0.265               # guard-ring centre line inside the generator's bounding box
RING_GAP = 0.8
TRACK = 0.9                 # channel track pitch
BUS = 1.0                   # side-bus pitch
MOS = {"nfet_01v8", "pfet_01v8", "pfet_01v8_lvt"}


class Dev:
    def __init__(self, name, model, w, l, rot=0, series=1, **nets):
        self.name, self.model, self.w, self.l, self.rot, self.series, self.nets = name, model, w, l, rot, series, nets


_cache = {}
def geom(d, bar="b"):
    """bar: the ring side ('b' bottom / 't' top, after rotation) that gets met1 (the rail bar side); the
    other ring lines stay li-only, so via pads and jumpers can come close to them."""
    key = (d.model, d.w, d.l, d.rot, d.series, bar)
    if key not in _cache:
        v = dict(viagb=0, viagt=0, viagl=0, viagr=0)
        if d.rot == 0:
            v["viagb" if bar == "b" else "viagt"] = 100
        elif d.rot == 270:          # original left -> bottom, right -> top
            v["viagl" if bar == "b" else "viagr"] = 100
        else:                       # 90: original right -> bottom, left -> top
            v["viagr" if bar == "b" else "viagl"] = 100
        hv = v
        if d.model in MOS:
            p = dict(w=d.w, l=d.l, nf=1, guard=1, full_metal=1, **hv)
        else:
            p = dict(w=d.w, l=d.l + 0.16, nx=d.series + 2, guard=1, **hv)
        g = probe_gencell("sky130_fd_pr__" + d.model, rot=d.rot, **p)
        g["params"] = p
        _cache[key] = g
    return _cache[key]


class Cell:
    def __init__(self, name):
        self.name, self.L = name, Layout(name)
        self.rows = []                 # dicts
        self.stubs = []                # (net, x, y, channel, side) side 'lo' = from the row below
        self.extra = []                # deferred paint commands (layer, box)

    # ------------------------------------------------------------------ placement
    def add_row(self, devs, rail, x0=0.0):
        self.rows.append(dict(devs_spec=devs, rail=rail, x0=x0))

    def _place(self, gaps):
        """Place all rows; gaps[i] = channel height between row i and i+1."""
        y = 0.0
        n = len(self.rows)
        for i, r in enumerate(self.rows):
            x = r["x0"]; placed = []
            r["bar"] = "t" if (i == n - 1 and n > 1) else "b"     # top row: rail bar on top (channel below)
            for d in r["devs_spec"]:
                g = geom(d, r["bar"])
                bx0, by0, bx1, by1 = g["bbox"]
                rl, rb, rr, rt = bx0 + INSET, by0 + INSET, bx1 - INSET, by1 - INSET
                ox, oy = x - rl, y - rb
                self.L.gencell("sky130_fd_pr__" + d.model, d.name, ox, oy, rot=d.rot, **g["params"])
                lab = {k: (vx + ox, vy + oy) for k, (vx, vy) in g["labels"].items()}
                placed.append(dict(dev=d, lab=lab, ring=(x, y, rr + ox, rt + oy), origin=(ox, oy), g=g))
                x = rr + ox + RING_GAP
            r.update(devs=placed, y=y, x1=placed[-1]["ring"][2], top=max(p["ring"][3] for p in placed))
            for p in placed:
                p["term"] = self._terms(p)
            if i < len(self.rows) - 1:
                y = r["top"] + gaps[i]

    def _terms(self, p):
        d, lab, ring = p["dev"], p["lab"], p["ring"]
        if d.model in MOS:
            g1 = lab["G"]
            cx, cy = (ring[0] + ring[2]) / 2, (ring[1] + ring[3]) / 2
            g2 = (2 * cx - g1[0], 2 * cy - g1[1])          # the opposite gate contact
            return {"D": lab["D"], "S": lab["S"], "G": [g1, g2]}
        n = d.series
        heads = []
        for i in range(n + 2):
            a, b = lab[f"R1_{i}"], lab[f"R2_{i}"]
            heads.append((a, b) if a[1] > b[1] else (b, a))
        yt, yb = heads[1][0][1] - 0.31, heads[1][1][1] + 0.26
        p["links"] = [(heads[k][0][0], heads[k + 1][0][0], yb if k % 2 == 1 else yt) for k in range(1, n)]
        p["dummy_heads"] = [heads[0], heads[n + 1]]
        end = heads[n][0] if n % 2 == 0 else heads[n][1]
        return {"P": (heads[1][0][0], yt), "M": (end[0], yt if n % 2 == 0 else yb)}

    # ------------------------------------------------------------------ connections
    def _connect(self):
        L = self.L
        uses = {}
        for r in self.rows:
            for p in r["devs"]:
                for n in p["dev"].nets.values():
                    uses[n] = uses.get(n, 0) + 1
        nrows = len(self.rows)
        for i, r in enumerate(self.rows):
            devs = r["devs"]
            if any(p["dev"].model.startswith("pfet") for p in devs):
                L.paint("nwell", r["x0"] - 0.45, r["y"] - 0.45, r["x1"] + 0.45, r["top"] + 0.45)
            r["bar_y"] = r["y"] if r["bar"] == "b" else r["top"]
            L.paint("metal1", r["x0"] - 0.12, r["bar_y"] - 0.12, r["x1"] + 0.12, r["bar_y"] + 0.12)   # rail bar
            if r["bar"] == "t":                                   # drops from shorter devices' ring tops
                for p in devs:
                    if p["ring"][3] < r["top"] - 0.01:
                        L.paint("metal1", p["ring"][0] - 0.12, p["ring"][3] - 0.12, p["ring"][2] + 0.12, p["ring"][3] + 0.12)
                        L.paint("metal1", p["ring"][0] - 0.12, p["ring"][3] - 0.12, p["ring"][0] + 0.12, r["top"] + 0.12)
            for p in devs:
                for (xa, xb, y) in p.get("links", []):
                    L.paint("metal1", xa - 0.125, y - 0.15, xb + 0.125, y + 0.15)
                for (top, bot) in p.get("dummy_heads", []):
                    L.paint("locali", top[0] - 0.15, top[1] - 0.3, top[0] + 0.15, p["ring"][3] + 0.085)
                    L.paint("locali", bot[0] - 0.15, p["ring"][1] - 0.085, bot[0] + 0.15, bot[1] + 0.3)
            jumped = set()
            for k in range(len(devs) - 1):
                a, b = devs[k], devs[k + 1]
                if a["dev"].model in MOS and b["dev"].model in MOS and a["dev"].rot == b["dev"].rot == 0:
                    na, nb = a["dev"].nets["S"], b["dev"].nets["D"]
                    if na == nb and na != r["rail"] and uses[na] == 2:
                        (xa, ya), (xb, yb) = a["term"]["S"], b["term"]["D"]
                        L.paint("metal1", xa - 0.12, min(ya, yb) - 0.2, xb + 0.12, min(ya, yb) + 0.2)
                        jumped |= {(id(a), "S"), (id(b), "D")}
            for p in devs:
                d = p["dev"]
                for t, pos in p["term"].items():
                    if (id(p), t) in jumped:
                        continue
                    net = d.nets[t]
                    if net == r["rail"]:
                        self._strap(p, t)
                        continue
                    if t == "G":
                        pos = self._gate_toward(p, i, nrows)
                    ch, side = self._channel_for(i, pos[1], r, nrows)
                    kind = "G" if t == "G" else "SD"
                    x, y = pos
                    if kind == "G" and d.rot == 0:          # move the pad off the gate strip, away from D/S
                        y = y + (0.07 if y > (p["ring"][1] + p["ring"][3]) / 2 else -0.07)
                    self._via(net, x, y, ch, side, kind, horizontal_gate=(kind == "G" and d.rot != 0))

    def _gate_toward(self, p, i, nrows):
        g1, g2 = p["term"]["G"]
        r = self.rows[i]
        want_up = (i == 0) or (i < nrows - 1 and g1[1] >= (r["y"] + r["top"]) / 2)
        if p["dev"].rot:                                     # side contacts: either one
            return g1 if g1[0] < g2[0] else g2
        if i == 0:
            return max(g1, g2, key=lambda q: q[1])
        if i == nrows - 1:
            return min(g1, g2, key=lambda q: q[1])
        return max(g1, g2, key=lambda q: q[1])

    def _channel_for(self, i, y, r, nrows):
        if i == 0:
            return 0, "lo"
        if i == nrows - 1:
            return i - 1, "hi"
        return (i, "lo") if y >= (r["y"] + r["top"]) / 2 else (i - 1, "hi")

    def _strap(self, p, t):
        """Rail terminal -> nearest ring line, on li."""
        L, ring = self.L, p["ring"]
        pts = p["term"][t] if t != "G" else p["term"]["G"]
        if t == "G":                                         # gate on the rail (dummies)
            best = None
            for (gx, gy) in pts:
                for line, dist in (("b", gy - ring[1]), ("t", ring[3] - gy), ("l", gx - ring[0]), ("r", ring[2] - gx)):
                    if best is None or dist < best[0]:
                        best = (dist, line, gx, gy)
            _, line, x, y = best
        else:
            x, y = pts
            dists = {"b": y - ring[1], "t": ring[3] - y, "l": x - ring[0], "r": ring[2] - x}
            line = min(dists, key=dists.get)
        if line in ("b", "t"):
            yr = ring[1] if line == "b" else ring[3]
            L.paint("locali", x - 0.2, min(y, yr) - 0.085, x + 0.2, max(y, yr) + 0.085)
        else:
            xr = ring[0] if line == "l" else ring[2]
            L.paint("locali", min(x, xr) - 0.085, y - 0.2, max(x, xr) + 0.085, y + 0.2)

    def _via(self, net, x, y, ch, side, kind, horizontal_gate=False):
        L = self.L
        if horizontal_gate:          # rotated device: the gate contact is a vertical strip
            hx, hy = 0.185, 0.215
        else:
            hx, hy = (0.185, 0.215) if kind == "SD" else (0.215, 0.185)
        L.paint("metal1", x - hx, y - hy, x + hx, y + hy)
        L.paint("via1", x - 0.13, y - 0.13, x + 0.13, y + 0.13)
        L.paint("metal2", x - 0.2, y - 0.2, x + 0.2, y + 0.2)
        self.stubs.append((net, x, y, ch, side))

    # ------------------------------------------------------------------ routing
    def _order(self, ch):
        st = [s for s in self.stubs if s[3] == ch]
        nets = sorted({s[0] for s in st})
        below = {n: set() for n in nets}
        for a in st:
            for b in st:
                if a[4] == "lo" and b[4] == "hi" and a[0] != b[0] and abs(a[1] - b[1]) < 0.8:
                    below[a[0]].add(b[0])
        order, temp, done = [], set(), set()
        def visit(n):
            if n in done: return
            if n in temp: raise RuntimeError(f"{self.name}: channel {ch} constraint cycle at {n}")
            temp.add(n)
            for m in sorted(below[n]): visit(m)
            temp.discard(n); done.add(n); order.append(n)
        for n in nets: visit(n)
        return order[::-1]

    def build(self, pins_left=(), pins_right=(), max_shift=6.0, no_pin=(), bus_ylo=None):
        """Two passes: count channel tracks (and shift rows sideways if a channel can't be ordered),
        then place, connect and route."""
        nch = len(self.rows) - 1
        # pass 1 with generous gaps
        for attempt in range(80):
            self.stubs = []; self.L = Layout(self.name)
            self._place([60.0] * nch); self._connect()
            try:
                orders = [self._order(c) for c in range(nch)]
                break
            except RuntimeError as e:
                c = int(str(e).split("channel ")[1].split()[0])
                self.rows[c + 1]["x0"] += 0.1
                if self.rows[c + 1]["x0"] > max_shift:
                    raise
        gaps = [len(o) * TRACK + 1.2 for o in orders]
        self.stubs = []; self.L = Layout(self.name)
        self._place(gaps); self._connect()
        orders = [self._order(c) for c in range(nch)]
        L = self.L
        xmin = min(r["x0"] for r in self.rows); xmax = max(r["x1"] for r in self.rows)
        # which nets need a side bus: used in more than one channel, a rail used in a channel, or a pin
        chans = {}
        for n, x, y, c, sd in self.stubs:
            chans.setdefault(n, set()).add(c)
        rails = {r["rail"] for r in self.rows}
        left = [n for n in sorted(chans) if (n in pins_left or len(chans[n]) > 1 or n == "VGND") and n not in pins_right and n != "VDPWR"]
        right = [n for n in sorted(chans) if (n in pins_right or (len(chans[n]) > 1 and n not in left) or n == "VDPWR") and n != "VGND"]
        # rail buses outermost, then signal buses
        bx = {}
        bx["VGND"] = xmin - 1.0 - BUS * (len(left) + 1)
        bx["VDPWR"] = xmax + 1.0 + BUS * (len(right) + 1)
        for k, n in enumerate([n for n in left if n != "VGND"]): bx[n] = xmin - 1.0 - BUS * (k + 1)
        for k, n in enumerate([n for n in right if n != "VDPWR"]): bx[n] = xmax + 1.0 + BUS * (k + 1)
        ylo = self.rows[0]["y"] - 1.0 if bus_ylo is None else bus_ylo
        yhi = self.rows[-1]["top"] + 1.5
        # channel tracks
        ty = {}
        for c in range(nch):
            ch0 = self.rows[c]["top"] + 0.6
            for k, n in enumerate(orders[c]):
                ty[(n, c)] = ch0 + 0.45 + k * TRACK
                xs = [s[1] for s in self.stubs if s[0] == n and s[3] == c]
                x0, x1 = min(xs), max(xs)
                if n in bx:
                    x0, x1 = min(x0, bx[n]), max(x1, bx[n])
                # track as wide as the via2 landing pads (0.5): narrower tracks leave < 0.3 um met3 notches
                # between neighbouring landings of the same net
                L.paint("metal3", x0 - 0.25, ty[(n, c)] - 0.25, x1 + 0.25, ty[(n, c)] + 0.25)
                if n in bx:
                    self._landing(bx[n], ty[(n, c)], rail=(n in rails))
        for n, x, y, c, sd in self.stubs:
            t = ty[(n, c)]
            L.paint("metal2", x - 0.15, min(y, t) - 0.15, x + 0.15, max(y, t) + 0.15)
            self._landing(x, t, rail=False)
        # buses
        for n, x in bx.items():
            layer = "metal1" if n in rails else "metal2"
            L.paint(layer, x - 0.2, ylo, x + 0.2, yhi)
        # rail bars to their buses
        for r in self.rows:
            xb = bx[r["rail"]]
            L.paint("metal1", min(xb, r["x0"]) - 0.12, r["bar_y"] - 0.12, max(xb, r["x1"]) + 0.12, r["bar_y"] + 0.12)
        # pins at the top end of the buses
        pins = []
        for n, x in bx.items():
            layer = "metal1" if n in rails else "metal2"
            if (n in rails or n in pins_left or n in pins_right) and n not in no_pin:
                pins.append((n, layer, (x - 0.2, yhi - 0.6, x + 0.2, yhi)))
        for k, (n, layer, b) in enumerate(pins, 1):
            L.pin(n, layer, *b, k)
        self.bus_x, self.tracks = bx, ty
        return self

    def _landing(self, x, y, rail=False):
        """via2 (>= 0.32 um: Magic drops smaller via2 silently) from a met3 track down to met2; for rail
        buses (met1) continue with via1."""
        L = self.L
        L.paint("metal2", x - 0.22, y - 0.22, x + 0.22, y + 0.22)
        L.paint("via2", x - 0.16, y - 0.16, x + 0.16, y + 0.16)
        L.paint("metal3", x - 0.25, y - 0.25, x + 0.25, y + 0.25)
        if rail:
            L.paint("via1", x - 0.13, y - 0.13, x + 0.13, y + 0.13)
            L.paint("metal1", x - 0.22, y - 0.22, x + 0.22, y + 0.22)

    def write(self):
        drc, errs, gds = self.L.run()
        return drc, errs, gds

    def placed(self, name):
        for r in self.rows:
            for p in r["devs"]:
                if p["dev"].name == name:
                    return p
