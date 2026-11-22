"""Scripted analog cells from rows of PDK devices + one routing channel (Magic, sky130A).

Model
-----
* A cell has a lower row ('lo', channel above it) and an upper row ('hi', channel below it), normally
  NMOS at the bottom (rail VGND) and PMOS at the top (rail VDPWR), with a routing channel in between.
* Every device is a PDK generator cell with its own guard ring. Neighbouring devices in a row are placed
  so that their guard rings overlap exactly, so each row has one merged ring (the rail, and the body).
  The ring has met1 only on its top and bottom edges (generator viagt/viagb); the vertical ring lines
  between devices are li only, so a met1 jumper can cross them.
* A terminal on the row's rail: met1 from its strip to the ring edge away from the channel.
* A net that joins only the right terminal of one device and the left terminal of its right-hand
  neighbour (series stacks): a direct met1 jumper across the shared ring line.
* Every other terminal: via1 + a met2 stub straight into the channel, to a horizontal met3 track of its
  net (one track per net). Stubs of different nets at the same x must not overlap, so the tracks are
  ordered by a vertical-constraint graph (a net reached from the lower row at x sits below a net reached
  from the upper row at the same x). A cycle raises an error.
* A rail of one row that is also used by terminals of the other row gets a tap stub from its ring.
* Pins: rails on the ring met1; signal pins at the left/right end of their met3 track.

Device spec (um):
    Dev("MN1", "nfet_01v8", 2, 2, D="nbias", G="nbias", S="VGND")
    Dev("R1", "res_xhigh_po_0p35", 0.35, 11, P="nr", M="VGND")     # P = top head, M = bottom head
MOS devices are drawn with D on the left and S on the right (nf = 1).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_lib import Layout, probe_gencell

RING_INSET = 0.265          # guard-ring centre line inside the generator's bounding box
RING_GAP = 0.8              # between the ring lines of neighbouring devices (Magic forbids overlapping subcell rings)
TRACK_PITCH = 0.9
MOS = {"nfet_01v8", "pfet_01v8", "pfet_01v8_lvt"}


class Dev:
    def __init__(self, name, model, w, l, series=1, **nets):
        """series (resistors only): number of unit strips in series inside one array (one dummy strip on
        each side). P is the top head of the first strip, M the free head of the last one."""
        self.name, self.model, self.w, self.l, self.series, self.nets = name, model, w, l, series, nets


_cache = {}
def geom(d):
    key = (d.model, d.w, d.l, d.series)
    if key not in _cache:
        if d.model in MOS:
            p = dict(w=d.w, l=d.l, nf=1, guard=1, full_metal=1, viagb=100, viagt=100, viagl=0, viagr=0)
        else:
            # one dummy strip on each side: a single 0.35 um strip's RPM marker is < 1.27 um (rpm.1)
            p = dict(w=d.w, l=d.l + 0.16, nx=d.series + 2, guard=1, viagb=100, viagt=100, viagl=0, viagr=0)
        g = probe_gencell("sky130_fd_pr__" + d.model, **p)
        g["params"] = p
        _cache[key] = g
    return _cache[key]


class Cell:
    def __init__(self, name):
        self.L = Layout(name)
        self.name = name
        self.stubs = []            # (net, x, y, which)
        self.pins = []
        self.rows = {}

    # ------------------------------------------------------------------ placement
    def row(self, which, devs, rail, x0=0.0, y=0.0):
        x = x0
        placed = []
        for d in devs:
            g = geom(d)
            bx0, by0, bx1, by1 = g["bbox"]
            rl, rb, rr, rt = bx0 + RING_INSET, by0 + RING_INSET, bx1 - RING_INSET, by1 - RING_INSET
            ox, oy = x - rl, y - rb
            self.L.gencell("sky130_fd_pr__" + d.model, d.name, ox, oy, **g["params"])
            lab = {k: (vx + ox, vy + oy) for k, (vx, vy) in g["labels"].items()}
            placed.append(dict(dev=d, lab=lab, ring=(x, y, rr + ox, rt + oy)))
            x = rr + ox + RING_GAP
        x1 = placed[-1]["ring"][2]
        r = self.rows[which] = dict(devs=placed, rail=rail, x0=x0, x1=x1, y=y,
                                     top=max(p["ring"][3] for p in placed))
        if which == "hi" and any(p["dev"].model.startswith("pfet") for p in placed):
            # one continuous n-well (separate wells 0.8 um apart violate nwell.2a)
            self.L.paint("nwell", x0 - 0.45, y - 0.45, x1 + 0.45, max(p["ring"][3] for p in placed) + 0.45)
        # rail bar: met1 along the ring edge away from the channel, joining every device's ring
        if which == "lo":
            self.L.paint("metal1", x0 - 0.12, y - 0.12, x1 + 0.12, y + 0.12)
        else:
            # upper row: ring tops differ with device height -> bar at the highest top, with a drop to each ring
            yt = r["top"]
            self.L.paint("metal1", x0 - 0.12, yt - 0.12, x1 + 0.12, yt + 0.12)
            for p in placed:
                if p["ring"][3] < yt - 0.01:
                    xm = (p["ring"][0] + p["ring"][2]) / 2
                    self.L.paint("metal1", p["ring"][0] - 0.12, p["ring"][3] - 0.12, p["ring"][0] + 0.12, yt + 0.12)
        # terminal positions
        for p in placed:
            d, lab, ring = p["dev"], p["lab"], p["ring"]
            if d.model in MOS:
                gy = lab["G"][1] if which == "lo" else ring[1] + (ring[3] - lab["G"][1])
                p["term"] = {"D": lab["D"], "S": lab["S"], "G": (lab["G"][0], gy)}
            else:
                # strips 1..n are the device (in series), strips 0 and n+1 are dummies (all terminals on the ring)
                n = d.series
                heads = []
                for i in range(n + 2):
                    a, b = lab[f"R1_{i}"], lab[f"R2_{i}"]
                    heads.append((a, b) if a[1] > b[1] else (b, a))       # (top, bottom)
                yt, yb = heads[1][0][1] - 0.31, heads[1][1][1] + 0.26
                p["links"] = []                                           # met1 bridges between active strips
                for k in range(1, n):
                    y = yb if k % 2 == 1 else yt
                    p["links"].append((heads[k][0][0], heads[k + 1][0][0], y))
                last_top = (n % 2 == 0) or n == 1 and False
                end = heads[n][0] if n % 2 == 0 else heads[n][1]
                p["term"] = {"P": (heads[1][0][0], yt),
                             "M": (end[0], yt if n % 2 == 0 else yb)}
                p["dummy_heads"] = [heads[0][::1], heads[n + 1]]
                p["dummy_heads"] = [(h[0], h[1]) for h in p["dummy_heads"]]
        return r

    # ------------------------------------------------------------------ connections
    def connect(self):
        """Rail straps, series jumpers and channel stubs for every terminal of every row."""
        L = self.L
        for which, r in self.rows.items():
            other = [o for o in self.rows if o != which]
            devs = r["devs"]
            jumped = set()
            # series jumpers: right terminal of device i and left terminal of device i+1 on the same net,
            # and that net used nowhere else
            uses = {}
            for rr in self.rows.values():
                for p in rr["devs"]:
                    for t, n in p["dev"].nets.items():
                        uses[n] = uses.get(n, 0) + 1
            for i in range(len(devs) - 1):
                a, b = devs[i], devs[i + 1]
                ta, tb = right_term(a), left_term(b)
                if ta and tb and a["dev"].nets[ta] == b["dev"].nets[tb] and uses[a["dev"].nets[ta]] == 2:
                    (xa, ya), (xb, yb) = a["term"][ta], b["term"][tb]
                    y = (ya + yb) / 2 if abs(ya - yb) < 0.2 else min(ya, yb)
                    L.paint("metal1", xa - 0.12, y - 0.2, xb + 0.12, y + 0.2)
                    jumped |= {(id(a), ta), (id(b), tb)}
            for p in devs:
                d, ring = p["dev"], p["ring"]
                for (xa, xb, y) in p.get("links", []):
                    L.paint("metal1", xa - 0.125, y - 0.15, xb + 0.125, y + 0.15)
                for (top, bot) in p.get("dummy_heads", []):
                    L.paint("locali", top[0] - 0.15, top[1] - 0.3, top[0] + 0.15, ring[3] + 0.085)
                    L.paint("locali", bot[0] - 0.15, ring[1] - 0.085, bot[0] + 0.15, bot[1] + 0.3)
                for t, (tx, ty) in p["term"].items():
                    if (id(p), t) in jumped:
                        continue
                    net = d.nets[t]
                    if net == r["rail"]:
                        self._strap(p, t, which)
                    else:
                        kind = "G" if (d.model in MOS and t == "G") else "SD"
                        if kind == "G":   # shift the pad away from the D/S strips (outward of the contact)
                            ty = ty + (0.07 if which == "lo" else -0.07)
                        self._via_stub(net, tx, ty, which, kind)
            # tap from this row's rail into the channel when the other row needs it
            for o in other:
                if any(r["rail"] in p["dev"].nets.values() for p in self.rows[o]["devs"]):
                    p0 = devs[0]; ring = p0["ring"]
                    yy = ring[3] if which == "lo" else ring[1]
                    self._via_stub(r["rail"], ring[0] + 0.3, yy, which)

    def _strap(self, p, t, which):
        """Terminal on the row's rail -> guard ring, on li (met1 straps would run too close to the
        gate-contact strips): D/S sideways to the nearest vertical ring line, a gate (dummies) from the
        far-side gate contact to the ring edge, a resistor head down/up to the ring."""
        L, ring, d = self.L, p["ring"], p["dev"]
        tx, ty = p["term"][t]
        if d.model in MOS and t in ("D", "S"):
            xr = ring[0] if t == "D" else ring[2]
            L.paint("locali", min(xr, tx) - 0.085, ty - 0.2, max(xr, tx) + 0.085, ty + 0.2)
        elif d.model in MOS and t == "G":
            gx = p["lab"]["G"][0]
            if which == "lo":       # bottom gate contact -> bottom ring line
                gy = ring[1] + (ring[3] - p["lab"]["G"][1])
                L.paint("locali", gx - 0.2, ring[1] - 0.085, gx + 0.2, gy)
            else:                   # top gate contact -> top ring line
                gy = p["lab"]["G"][1]
                L.paint("locali", gx - 0.2, gy, gx + 0.2, ring[3] + 0.085)
        else:                       # resistor head -> ring edge on its side
            yr = ring[3] if ty > (ring[1] + ring[3]) / 2 else ring[1]
            L.paint("locali", tx - 0.15, min(ty, yr) - 0.085, tx + 0.15, max(ty, yr) + 0.085)

    def _via_stub(self, net, x, y, which, kind="SD"):
        """via1 + met2 landing. Pads are as small as the enclosure rules allow (narrow devices have the
        gate-contact strips 0.16 um from the D/S strips): D/S 0.37 x 0.43, gate 0.43 x 0.37 (um)."""
        L = self.L
        hx, hy = (0.185, 0.215) if kind == "SD" else (0.215, 0.185)
        L.paint("metal1", x - hx, y - hy, x + hx, y + hy)
        L.paint("via1", x - 0.13, y - 0.13, x + 0.13, y + 0.13)
        L.paint("metal2", x - 0.2, y - 0.2, x + 0.2, y + 0.2)
        self.stubs.append((net, x, y, which))

    # ------------------------------------------------------------------ routing
    def channel_order(self):
        nets = sorted({s[0] for s in self.stubs})
        below = {n: set() for n in nets}
        for a in self.stubs:
            for b in self.stubs:
                if a[3] == "lo" and b[3] == "hi" and a[0] != b[0] and abs(a[1] - b[1]) < 0.8:
                    below[a[0]].add(b[0])
        order, temp, done = [], set(), set()
        def visit(n):
            if n in done: return
            if n in temp: raise RuntimeError(f"{self.name}: channel constraint cycle at net {n}")
            temp.add(n)
            for m in sorted(below[n]): visit(m)
            temp.discard(n); done.add(n); order.append(n)
        for n in nets: visit(n)
        return order[::-1]

    def channel_height(self):
        return len({s[0] for s in self.stubs}) * TRACK_PITCH + 1.2

    def route(self, pins_left=(), pins_right=()):
        lo, hi = self.rows["lo"], self.rows["hi"]
        ch0, ch1 = lo["top"] + 0.6, hi["y"] - 0.6
        order = self.channel_order()
        need = len(order) * TRACK_PITCH
        if ch1 - ch0 < need:
            raise RuntimeError(f"{self.name}: channel needs {need:.1f} um, has {ch1 - ch0:.1f}")
        ty = {n: ch0 + 0.45 + i * TRACK_PITCH for i, n in enumerate(order)}
        L = self.L
        xmin = min(r["x0"] for r in self.rows.values()); xmax = max(r["x1"] for r in self.rows.values())
        for n in order:
            xs = [s[1] for s in self.stubs if s[0] == n]
            x0, x1 = min(xs), max(xs)
            if n in pins_left: x0 = xmin - 1.0
            if n in pins_right: x1 = xmax + 1.0
            L.paint("metal3", x0 - 0.2, ty[n] - 0.15, x1 + 0.2, ty[n] + 0.15)
            if n in pins_left:
                self.pins.append((n, "metal3", (x0 - 0.2, ty[n] - 0.15, x0 + 0.4, ty[n] + 0.15)))
            if n in pins_right:
                self.pins.append((n, "metal3", (x1 - 0.4, ty[n] - 0.15, x1 + 0.2, ty[n] + 0.15)))
        for n, x, y, which in self.stubs:
            L.paint("metal2", x - 0.15, min(y, ty[n]) - 0.15, x + 0.15, max(y, ty[n]) + 0.15)
            # via2 drawn >= 0.32 um: Magic silently drops a smaller via2 contact (no cut in the GDS,
            # no DRC error) - found 2026-11-12, every channel connection was open
            L.paint("metal2", x - 0.22, ty[n] - 0.22, x + 0.22, ty[n] + 0.22)
            L.paint("via2", x - 0.16, ty[n] - 0.16, x + 0.16, ty[n] + 0.16)
            L.paint("metal3", x - 0.25, ty[n] - 0.25, x + 0.25, ty[n] + 0.25)
        self.tracks = ty
        return ty

    # ------------------------------------------------------------------ pins + output
    def rail_pin(self, which, net):
        r = self.rows[which]
        ring = r["devs"][0]["ring"]
        y = ring[1] if which == "lo" else ring[3]
        self.pins.append((net, "metal1", (ring[0] + 0.3, y - 0.1, ring[0] + 1.3, y + 0.1)))

    def write(self):
        for i, (net, layer, (x0, y0, x1, y1)) in enumerate(self.pins, 1):
            self.L.pin(net, layer, x0, y0, x1, y1, i)
        return self.L.run()


def left_term(p):
    return "D" if p["dev"].model in MOS else None


def right_term(p):
    return "S" if p["dev"].model in MOS else None
