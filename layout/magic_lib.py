"""Small helpers for scripted layout in Magic (sky130A). Used by the layout/gen_*.py generators.

A generator builds a list of Tcl commands with these helpers, then run() writes the Tcl file,
runs Magic in batch mode and saves <cell>.mag + layout/cells/<cell>.gds. Coordinates are in um.
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDK = os.environ.get("PDK_ROOT", "/usr/local/share/pdk")
RC = os.path.join(PDK, "sky130A", "libs.tech", "magic", "sky130A.magicrc")
CELLS = os.path.join(ROOT, "layout", "cells")
WORK = os.path.join(ROOT, "sim", "out", "layout", "gen")


def f(x):
    return f"{x:.3f}um"


class Layout:
    def __init__(self, cell):
        self.cell = cell
        self.t = ["drc off", "snap internal", f"cellname rename (UNNAMED) {cell}", "edit"]

    def box(self, x0, y0, x1, y1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
        self.t.append(f"box {f(x0)} {f(y0)} {f(x1)} {f(y1)}")

    def paint(self, layer, x0, y0, x1, y1):
        self.box(x0, y0, x1, y1); self.t.append(f"paint {layer}")

    def wire(self, layer, x0, y0, x1, y1, w):
        """Straight horizontal or vertical wire of width w between two centre points."""
        h = w / 2
        if abs(y1 - y0) < 1e-9:
            self.paint(layer, min(x0, x1) - h, y0 - h, max(x0, x1) + h, y0 + h)
        elif abs(x1 - x0) < 1e-9:
            self.paint(layer, x0 - h, min(y0, y1) - h, x0 + h, max(y0, y1) + h)
        else:
            raise ValueError("wire must be horizontal or vertical")

    STACK = [("locali", "mcon"), ("metal1", "via1"), ("metal2", "via2"), ("metal3", "via3"), ("metal4", None)]

    def via(self, x, y, lo, hi, size=0.5, pad=0.8):
        """Via stack centred at (x, y) from layer lo to layer hi (names as in STACK), with metal pads."""
        names = [n for n, _ in self.STACK]
        i0, i1 = names.index(lo), names.index(hi)
        for i in range(i0, i1 + 1):
            self.paint(names[i], x - pad / 2, y - pad / 2, x + pad / 2, y + pad / 2)
        for i in range(i0, i1):
            cut = self.STACK[i][1]
            self.paint(cut, x - size / 2, y - size / 2, x + size / 2, y + size / 2)

    def gencell(self, gtype, name, x, y, **params):
        """Place a PDK device generator cell with its lower-left corner at (x, y)."""
        p = " ".join(f"{k} {v}" for k, v in params.items())
        self.t += [f"box {f(x)} {f(y)} {f(x)} {f(y)}", f"magic::gencell sky130::{gtype} {name} {p}"]

    def place(self, name, x, y):
        """Move an already placed instance so its bounding box starts at (x, y)."""
        self.t += [f"select cell {name}", f"move to {f(x)} {f(y)}"]

    def pin(self, net, layer, x0, y0, x1, y1, idx):
        self.paint(layer, x0, y0, x1, y1)
        self.t += [f"label {net} FreeSans 0.2u -{layer}", f"port make {idx}"]

    def run(self, extra=()):
        os.makedirs(CELLS, exist_ok=True); os.makedirs(WORK, exist_ok=True)
        gds = os.path.join(CELLS, f"{self.cell}.gds")
        t = self.t + list(extra) + [
            "select top cell", "drc on", "drc check", "drc catchup",
            'puts "DRC_COUNT [drc list count total]"',
            f"cd {WORK}", f"save {self.cell}",
            f"gds write {gds}", "quit -noprompt"]
        tcl = os.path.join(WORK, f"{self.cell}.tcl")
        open(tcl, "w").write("\n".join(t) + "\n")
        r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", RC, tcl],
                           capture_output=True, text=True, cwd=WORK)
        log = r.stdout + r.stderr
        open(os.path.join(WORK, f"{self.cell}.log"), "w").write(log)
        m = re.search(r"DRC_COUNT (\d+)", log)
        errs = [l for l in log.splitlines() if re.search(r"\berror\b|Error", l)][:10]
        return (int(m.group(1)) if m else -1), errs, gds
