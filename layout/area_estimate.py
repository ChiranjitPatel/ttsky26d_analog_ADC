#!/usr/bin/env python3
"""Footprint estimate per block from its SPICE netlist (drawn devices only, no routing).

Per-device footprints (um^2), deliberately generous:
  MOSFET        (W + 1.0) * (L + 1.2) per instance x mult     (diffusion ends, contacts, poly ext.)
  res_xhigh_po  (0.35 + 1.4) * (L + 3.0)                       (poly heads + spacing)
  pnp 3.4x3.4   11 * 11 per device                             (emitter + base + collector rings)
  MIM m3        (W + 1.0) * (L + 1.0) x MF                     (capm spacing / met3 enclosure)
Block area = devices x ROUTING (analog 2.0, regular arrays 1.3), sub-cells counted where instantiated.
"""
import os, re, json
N = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim", "out", "netlist")
def parse(cell):
    txt = open(os.path.join(N, cell + ".spice")).read().replace("\n+", " ")
    m = re.search(rf"^\.subckt {cell}\b.*?^\.ends", txt, re.S | re.M)
    body = m.group(0).splitlines()[1:-1]
    a, subs = 0.0, []
    for ln in body:
        if not ln or ln[0] in "*.": continue
        f = ln.split(); kv = dict(x.split("=", 1) for x in f if "=" in x)
        g = lambda k, d=1.0: float(kv.get(k, kv.get(k.upper(), d)))
        model = next((x for x in f if x.startswith("sky130_fd_pr__")), None)
        mult = g("mult", g("m", 1.0))
        if model is None:
            subs.append(f[-1]); continue
        if "fet" in model:
            a += (g("W") + 1.0) * (g("L") + 1.2) * mult
        elif "res_xhigh" in model:
            a += 1.75 * (g("L") + 3.0) * mult
        elif "pnp" in model:
            a += 121.0 * mult
        elif "cap_mim" in model:
            a += (g("W") + 1.0) * (g("L") + 1.0) * g("MF")
    return a, subs
cells = ["bias_gen", "ota", "bandgap_core", "ptat_out", "vref_filt", "vref_buf", "vref_sel",
         "comparator", "inmux", "vcm_gen", "dac_sw", "cap_dac"]
dev = {}
for c in cells:
    a, subs = parse(c)
    for s in subs:
        if s in dev: a += dev[s]          # include sub-cells already computed (ota in bandgap, dac_sw in DAC)
    dev[c] = a
for c in cells: print(f"{c:13s} devices {dev[c]:8.0f} um^2")
json.dump(dev, open(os.path.join(N, "..", "area_estimate.json"), "w"), indent=1)
