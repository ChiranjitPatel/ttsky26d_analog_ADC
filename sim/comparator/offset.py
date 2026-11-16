#!/usr/bin/env python3
"""Toggle point of the comparator from tb_offset.spice: inp at which the decision (onb vs opb at the end of each
evaluate phase) flips, for the schematic and the extracted layout. Offset = toggle point - inn (0.716 V)."""
import os
import numpy as np
d = np.loadtxt(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "comparator", "offset.dat"), skiprows=1)
t, inp = d[:, 0], d[:, 2]
ends = np.arange(99e-9, 40e-6, 100e-9)                  # just before clkb rises again
k = np.searchsorted(t, ends)
k = k[k < len(t)]
for name, cop, con in (("schematic", 3, 4), ("layout", 5, 6)):
    dec = d[k, con] > d[k, cop]
    flips = np.where(dec[1:] != dec[:-1])[0]
    tp = [inp[k[i + 1]] for i in flips]
    print(f"{name}: decisions flip at inp = {', '.join(f'{x:.4f}' for x in tp) or 'never'} V; "
          f"offset {', '.join(f'{(x - 0.716) * 1e3:+.1f}' for x in tp)} mV")
