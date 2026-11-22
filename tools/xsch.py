#!/usr/bin/env python3
"""Tiny helper to write xschem schematics (.sch) and symbols (.sym) from Python.

Every device pin gets a short wire stub with a `lab_pin` net label at its end, so connectivity
is by net name. The result is a valid xschem schematic that netlists correctly; tidy the
drawing in the xschem GUI if you like — connectivity doesn't change when you add wires.

Usage (see xschem/gen_*.py):
    s = Schematic()
    s.port("VDPWR", "inout"); s.port("pd", "in"); s.port("nbias", "out")
    s.dev("sky130_fd_pr/nfet_01v8.sym", "MN1", {"D": "nbias", "G": "nbias", "S": "VGND", "B": "VGND"},
          W=2, L=2, nf=1, mult=1)
    s.write("xschem/bias_gen.sch", sym=True)
"""
import os
import re

PDK_XSCHEM = os.path.join(os.environ.get("PDK_ROOT", "/usr/local/share/pdk"), "sky130A", "libs.tech", "xschem")
XSCHEM_DEVICES = "/usr/local/share/xschem/xschem_library/devices"
PROJECT_XSCHEM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "xschem")
SEARCH = [PROJECT_XSCHEM, PDK_XSCHEM, XSCHEM_DEVICES, os.path.dirname(XSCHEM_DEVICES)]

_PIN = re.compile(r"^B 5 (\S+) (\S+) (\S+) (\S+) \{([^}]*)\}", re.M)


def sym_pins(sym):
    """Return {pin_name: (x, y)} for a symbol, from its 'B 5' pin boxes."""
    for d in SEARCH:
        p = os.path.join(d, sym)
        if os.path.exists(p):
            break
    else:
        raise FileNotFoundError(sym)
    pins = {}
    for x1, y1, x2, y2, attrs in _PIN.findall(open(p).read()):
        name = re.search(r"name=(\S+)", attrs).group(1)
        pins[name] = ((float(x1) + float(x2)) / 2, (float(y1) + float(y2)) / 2)
    return pins


def _fmt(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


class Schematic:
    def __init__(self, cols=5, dx=380, dy=280):
        self.lines = []
        self.ports = []  # (name, dir)
        self.n = 0
        self.cols, self.dx, self.dy = cols, dx, dy
        self.nlab = 0
        self.texts = []

    def _next_xy(self):
        x = (self.n % self.cols) * self.dx
        y = (self.n // self.cols) * self.dy + 200
        self.n += 1
        return x, y

    def _label(self, x, y, net, flip=0):
        self.nlab += 1
        self.lines.append(f"C {{lab_pin.sym}} {x:g} {y:g} 0 {flip} {{name=p{self.nlab} sig_type=std_logic lab={net}}}")

    def port(self, name, direction):
        """direction: in | out | inout"""
        sym = {"in": "ipin.sym", "out": "opin.sym", "inout": "iopin.sym"}[direction]
        y = -200 + 40 * len(self.ports)
        self.ports.append((name, direction))
        self.lines.append(f"C {{{sym}}} -400 {y} 0 0 {{name=p_{name} lab={name}}}")

    def dev(self, sym, name, conn, **params):
        x, y = self._next_xy()
        pins = sym_pins(sym)
        missing = set(pins) - set(conn)
        if missing:
            raise ValueError(f"{name}: unconnected pins {missing}")
        attrs = " ".join([f"name={name}"] + [f"{k}={_fmt(v)}" for k, v in params.items()])
        self.lines.append(f"C {{{sym}}} {x} {y} 0 0 {{{attrs}}}")
        for pin, net in conn.items():
            px, py = pins[pin]
            ax, ay = x + px, y + py
            # short wire stub pointing away from the symbol, label at its end
            # box-symbol pins (|x| >= 40) always get horizontal stubs: on tall symbols, pins near the
            # corners have |y| > |x| and vertical stubs along the same x would overlap and short
            if abs(px) >= 40 or abs(px) >= abs(py):
                if px < 0:
                    bx, by, flip = ax - 40, ay, 0
                else:  # right side: go past the device's attribute text, text to the right
                    bx, by, flip = ax + 110, ay, 1
            else:
                bx, by, flip = ax, ay + (40 if py > 0 else -40), 0
            self.lines.append(f"N {ax:g} {ay:g} {bx:g} {by:g} {{lab={net}}}")
            self._label(bx, by, net, flip)

    def text(self, s):
        self.texts.append(s)

    def code(self, name, value):
        """Embed a code block (e.g. .include) — only for testbench schematics."""
        x, y = self._next_xy()
        self.lines.append(f"C {{code_shown.sym}} {x} {y} 0 0 {{name={name} only_toplevel=false value=\"{value}\"}}")

    def write(self, path, sym=False, header=""):
        out = ["v {xschem version=3.4.8RC file_version=1.2}", f"G {{}}", "K {}", "V {}", "S {}", "E {}"]
        for i, t in enumerate(([header] if header else []) + self.texts):
            out.append(f"T {{{t}}} -400 {-400 - 30 * i} 0 0 0.3 0.3 {{}}")
        out += self.lines
        with open(path, "w") as f:
            f.write("\n".join(out) + "\n")
        if sym:
            self.write_symbol(os.path.splitext(path)[0] + ".sym")

    def write_symbol(self, path):
        """Box symbol: inputs and inouts on the left, outputs on the right."""
        left = [p for p in self.ports if p[1] != "out"]
        right = [p for p in self.ports if p[1] == "out"]
        h = 20 * max(len(left), len(right), 1) + 20
        name = os.path.splitext(os.path.basename(path))[0]
        out = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
               "K {type=subcircuit\nformat=\"@name @pinlist @symname\"\ntemplate=\"name=x1\"\n}",
               "V {}", "S {}", "E {}",
               f"B 4 -60 -{h/2:g} 60 {h/2:g} {{}}",
               f"T {{@symname}} -55 -{h/2 + 20:g} 0 0 0.25 0.25 {{}}",
               f"T {{@name}} -55 {h/2 + 5:g} 0 0 0.25 0.25 {{}}"]
        for side, pins, sx in (("l", left, -80), ("r", right, 80)):
            for i, (pn, d) in enumerate(pins):
                y = -h / 2 + 20 + 20 * i
                edge = -60 if side == "l" else 60
                out.append(f"L 4 {sx} {y:g} {edge} {y:g} {{}}")
                out.append(f"B 5 {sx - 2.5:g} {y - 2.5:g} {sx + 2.5:g} {y + 2.5:g} {{name={pn} dir={d}}}")
                tx = edge + (5 if side == "l" else -5)
                out.append(f"T {{{pn}}} {tx} {y - 6:g} 0 {0 if side == 'l' else 1} 0.2 0.2 {{}}")
        with open(path, "w") as f:
            f.write("\n".join(out) + "\n")
