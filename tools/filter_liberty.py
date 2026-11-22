#!/usr/bin/env python3
"""Write a copy of a liberty file without the cells we never want from synthesis
(power-gating/isolation 'lpflow', probes, tap/fill/decap, clock-gating, sizing-only '_0' variants).
Usage: filter_liberty.py in.lib out.lib"""
import re, sys
BAD = re.compile(r"sky130_fd_sc_hd__(lpflow_|probe_|tap|fill|decap|diode|dlygate|clkdlybuf|einv|ebuf|sdlclk|dlclkp|.*_0$)")
src = open(sys.argv[1]).read()
out, i, dropped = [], 0, 0
for m in re.finditer(r'cell\s*\(\s*"?([A-Za-z0-9_]+)"?\s*\)\s*\{', src):
    if m.start() < i:
        continue
    name = m.group(1)
    if not BAD.match(name):
        continue
    # copy up to the cell, then skip the cell body by brace matching
    out.append(src[i:m.start()]); depth = 0; j = m.end() - 1
    while True:
        c = src[j]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    i = j + 1; dropped += 1
out.append(src[i:])
open(sys.argv[2], "w").write("".join(out))
print(f"dropped {dropped} cells")
