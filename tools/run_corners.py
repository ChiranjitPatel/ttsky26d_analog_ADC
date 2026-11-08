#!/usr/bin/env python3
"""Phase 2 runner: run an existing testbench across process corners, temperatures and supplies.

Usage (from the testbench's directory):
    ../../tools/run_corners.py tb_bandgap.spice [--corners tt,ff,ss,fs,sf] [--temps -40,27,125]
                               [--vdd 1.62,1.8,1.98] [--jobs 4] [--mc N --mc-corner tt_mm]
For each combination it writes a copy of the testbench into ../out/corners/<tb>/<tag>/ with
  * '.lib .../sky130.lib.spice tt'  -> the corner
  * '.temp 27'                      -> the temperature
  * every supply source 'V<name> <node> 0 [dc] 1.8 ...' whose name starts with VDD, '.param vdd=1.8'
    and supply ramps 'alter @VDD[pulse] = [ 0 1.8 ...' -> the supply value
  * relative paths '../out/...' rewritten so outputs land in that run's own directory
runs ngspice (num_threads = 1, in parallel), and collects every "name = value" line that ngspice
prints (meas results and print statements) into ../out/corners/<tb>/results.csv.
Monte Carlo: --mc N runs N copies of --mc-corner (a *_mm library section, mismatch on) with different
random seeds.
"""
import argparse, csv, itertools, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument("tb")
ap.add_argument("--corners", default="tt,ff,ss,fs,sf")
ap.add_argument("--temps", default="27")
ap.add_argument("--vdd", default="1.8")
ap.add_argument("--jobs", type=int, default=4)
ap.add_argument("--mc", type=int, default=0)
ap.add_argument("--mc-corner", default="tt_mm")
a = ap.parse_args()

here = os.getcwd()
src = open(a.tb).read()
name = os.path.splitext(os.path.basename(a.tb))[0]
base = os.path.abspath(os.path.join(here, "..", "out", "corners", name))
os.makedirs(base, exist_ok=True)
lib_re = re.compile(r"^(\.lib\s+\S*sky130\.lib\.spice)\s+\w+\s*$", re.M)
if not lib_re.search(src):
    sys.exit("no '.lib .../sky130.lib.spice <corner>' line found")
vdd_re = re.compile(r"^(V(?:DD|dd)\w*\s+\S+\s+0\s+(?:dc\s+)?)1\.8\b", re.M)

jobs = []
if a.mc:
    for seed in range(1, a.mc + 1):
        jobs.append((f"{a.mc_corner}_s{seed}", a.mc_corner, "27", "1.8", seed))
else:
    for c, t, v in itertools.product(a.corners.split(","), a.temps.split(","), a.vdd.split(",")):
        jobs.append((f"{c}_T{t}_V{v}", c, t, v, None))

def make(tag, corner, temp, vdd, seed):
    d = os.path.join(base, tag); os.makedirs(d, exist_ok=True)
    s = lib_re.sub(lambda m: f"{m.group(1)} {corner}", src)
    s = re.sub(r"^\.temp\s+\S+", f".temp {temp}", s, flags=re.M)
    s = vdd_re.sub(lambda m: m.group(1) + vdd, s)
    s = re.sub(r"^(\.param\s+vdd\s*=\s*)1\.8\b", lambda m: m.group(1) + vdd, s, flags=re.M)
    # supply ramps written in .control as 'alter @VDD[pulse] = [ 0 1.8 ...'
    s = re.sub(r"(@VDD\[pulse\]\s*=\s*\[\s*0\s+)1\.8\b", lambda m: m.group(1) + vdd, s)
    s = s.replace("../out/netlist/", os.path.abspath(os.path.join(here, "..", "out", "netlist")) + "/")
    s = re.sub(r"\.\./out/[\w/]+/", d + "/", s)
    f = os.path.join(d, "tb.spice"); open(f, "w").write(s)
    # each run needs the .spiceinit next to it. The Monte Carlo seed goes there: the mismatch
    # parameters (agauss) are drawn while the netlist is parsed, i.e. before .control runs.
    init = open(os.path.join(here, ".spiceinit")).read() if os.path.exists(os.path.join(here, ".spiceinit")) else ""
    if seed is not None:
        init += f"\nset rndseed={seed}\n"
    open(os.path.join(d, ".spiceinit"), "w").write(init)
    return d

def run(job):
    tag = job[0]; d = make(*job)
    env = dict(os.environ, OMP_NUM_THREADS="1")
    with open(os.path.join(d, "log.txt"), "w") as lg:
        rc = subprocess.call(["ngspice", "-b", "tb.spice"], cwd=d, stdout=lg, stderr=subprocess.STDOUT, env=env)
    vals = {}
    for line in open(os.path.join(d, "log.txt"), errors="ignore"):
        m = re.match(r"^\s*([A-Za-z_][\w().\[\]@#]*)\s*=\s*([-+0-9.eE]+)", line)
        if m:
            vals[m.group(1)] = m.group(2)
    return tag, job, rc, vals

with ThreadPoolExecutor(a.jobs) as ex:
    results = list(ex.map(run, jobs))
keys = sorted({k for _, _, _, v in results for k in v})
with open(os.path.join(base, "results.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["tag", "corner", "temp", "vdd", "seed", "rc"] + keys)
    for tag, (t_, c, T, V, sd), rc, v in results:
        w.writerow([tag, c, T, V, sd if sd is not None else "", rc] + [v.get(k, "") for k in keys])
print(f"{len(results)} runs -> {os.path.join(base, 'results.csv')}")
bad = [r[0] for r in results if r[2] != 0]
if bad:
    print("non-zero exit:", " ".join(bad))
