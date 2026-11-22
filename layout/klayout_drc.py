#!/usr/bin/env python3
"""KLayout DRC with the TT precheck deck (layout/drc/sky130A_mr.drc, copied from tt-support-tools
precheck/tech-files): runs the feol, beol and offgrid checks on a GDS, like the TT precheck does.
KLayout runs in the LibreLane container (ghcr.io/librelane/librelane:3.0.17, KLayout 0.30.7; the
precheck uses 0.30.4). Needs the Docker daemon (start it with: dockerd &).
Usage: python3 layout/klayout_drc.py layout/cells/bias_gen.gds      (reports in sim/out/layout/<cell>/)
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE = "ghcr.io/librelane/librelane:3.0.17"
gds = os.path.abspath(sys.argv[1])
cell = os.path.splitext(os.path.basename(gds))[0]
out = os.path.join(ROOT, "sim", "out", "layout", cell)
os.makedirs(out, exist_ok=True)
total = 0
for check in ("feol", "beol", "offgrid"):
    rep = os.path.join(out, f"klayout_{check}.xml")
    cmd = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", ROOT, IMAGE,
           "klayout", "-b", "-r", os.path.join(ROOT, "layout", "drc", "sky130A_mr.drc"),
           "-rd", f"{check}=true", "-rd", f"input={gds}", "-rd", "thr=1", "-rd", f"report={rep}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    open(os.path.join(out, f"klayout_{check}.log"), "w").write(r.stdout + r.stderr)
    if r.returncode != 0 or not os.path.exists(rep):
        print(f"KLayout {check}: FAILED to run (see {out}/klayout_{check}.log)"); total += 1; continue
    xml = open(rep).read()
    n = len(re.findall(r"<item>", xml))
    cats = sorted(set(re.findall(r"<category>'?([^<']+)'?</category>", xml)))
    print(f"KLayout {check}: {n} errors" + (f"  {cats[:8]}" if n else ""))
    total += n
sys.exit(0 if total == 0 else 1)
