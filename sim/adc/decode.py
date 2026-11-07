#!/usr/bin/env python3
"""Decode the ADC codes at each EOC from an adc_core run (make_tb.py) and compare them with the ideal
code floor(256 * vin / VREF). VREF = 1.215 V (ideal) or, for --real-ref runs, the simulated vref at the
sampling instant (last column of the data file).
Usage: decode.py name
"""
import sys
import numpy as np

name = sys.argv[1]
d = np.loadtxt(f"../out/adc/{name}.dat", skiprows=1)
t, eoc, smpt = d[:, 0], d[:, 2], d[:, 6]
bits = d[:, 7:15]
vref_col = d[:, 15] if d.shape[1] > 15 else None
vins = [float(x) for x in open(f"../out/adc/{name}_vin.txt")]

rise = np.where((eoc[:-1] < 0.9) & (eoc[1:] >= 0.9))[0]
falls = np.where((smpt[:-1] > 0.9) & (smpt[1:] <= 0.9))[0]       # sampling instants
rows = []
for i, k in enumerate(rise):
    if i >= len(vins):
        break
    kk = int(np.argmin(abs(t - (t[k] + 0.2e-6))))   # 0.2 us after EOC rises (adaptive steps: don't count samples)
    code = int(sum(int(bits[kk, b] > 0.9) << b for b in range(8)))
    vref = 1.215
    if vref_col is not None:
        prior = falls[falls < k]
        vref = vref_col[prior[-1]] if len(prior) else vref_col[k]
    ideal = min(max(int(np.floor(256 * vins[i] / vref)), 0), 255)
    exact = 256 * vins[i] / vref
    rows.append((vins[i], vref, code, ideal, exact))

for v, vr, c, ideal, exact in rows:
    print(f"vin={v:.5f} V  vref={vr:.4f} V  code={c:3d}  ideal={ideal:3d} ({exact:7.2f})  err={c - ideal:+d}")
print(f"{len(rows)} conversions decoded")
