#!/usr/bin/env python3
"""Monte Carlo statistics for tb_bandgap_mc-style runs: python3 mc_stats.py <tb name> [...]
Drops non-converged seeds (VBG outside 0.5-2 V) and reports them."""
import csv, sys, numpy as np
for name in sys.argv[1:]:
    r = list(csv.DictReader(open(f"../out/corners/{name}/results.csv")))
    bad = [x["tag"] for x in r if not 0.5 < float(x["v(vbg)"] or 0) < 2]
    r = [x for x in r if 0.5 < float(x["v(vbg)"] or 0) < 2]
    v = np.array([float(x["v(vbg)"]) for x in r]); d = np.array([float(x["dv_in"]) for x in r])
    tc = np.array([(float(x["vbg125"]) - float(x["vbgm40"])) for x in r])
    print(f"{name:22s} n={len(v):3d} VBG mean {v.mean():.4f} V  sd {v.std(ddof=1)*1e3:5.1f} mV  "
          f"[{v.min():.3f}, {v.max():.3f}]  dv_in sd {d.std(ddof=1)*1e3:.2f} mV  "
          f"VBG(125)-VBG(-40) sd {tc.std(ddof=1)*1e3:.1f} mV  non-converged: {bad}")
