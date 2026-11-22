#!/usr/bin/env python3
"""Waveform plots of the M2 whole-tile runs, schematic (sch) and extracted layout (rc) overlaid.
Reads ../out/m2/{sch,rc}.dat (make_tb.py) and ../out/m2/scen_<name>_{sch,rc}.dat (scenarios.py); writes
plots/conversions.png and plots/scenarios.png. Columns: make_tb.py time clk eoc vsrc pad0 pin1 d0..d7;
scenarios.py time clk eoc vsrc pad0 pin1 cmp d0..d7.
Usage: python3 plot.py"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

H = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(H, "..", "out", "m2")
os.makedirs(os.path.join(H, "plots"), exist_ok=True)
STYLE = {"sch": dict(color="C0", lw=1.4, label="schematic"), "rc": dict(color="C3", lw=1.0, ls="--", label="extracted layout")}


def load(name):
    f = os.path.join(OUT, name)
    return np.loadtxt(f, skiprows=1) if os.path.exists(f) else None


def code(d, b0):
    return sum((d[:, b0 + b] > 0.9).astype(int) << b for b in range(8))


# ---- 5 conversions on ua[0]
fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
for dut in ("sch", "rc"):
    d = load(f"{dut}.dat")
    if d is None:
        continue
    t = d[:, 0] * 1e6
    if dut == "sch":
        ax[0].plot(t, d[:, 3], "k", lw=1, label="source")
    ax[0].plot(t, d[:, 4], **{**STYLE[dut], "label": f"ua[0] pad ({STYLE[dut]['label']})"})
    ax[1].plot(t, code(d, 6), **STYLE[dut])
    ax[2].plot(t, d[:, 2] + (0 if dut == "sch" else 0.05), **STYLE[dut])
ax[0].set(ylabel="V", title="M2 whole tile: 5 conversions, internal reference, clk 1 MHz (tt, 27 °C, 1.8 V)")
ax[1].set(ylabel="D[7:0] (uo_out)")
ax[2].set(ylabel="EOC (uio_out[5]) [V]", xlabel="t [µs]")
for a in ax:
    a.grid(alpha=0.3); a.legend(fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(H, "plots", "conversions.png"), dpi=90)

# ---- operating scenarios
SC = [("gnd", "VGND input (INSEL = 11) + VREF on ua[1]", "pin1"), ("vptat", "Temperature sensor (INSEL = 01), 100 kHz", None),
      ("vbg", "Bandgap via ADC (REF_SEL = 1, 1.5 V on ua[1]), 100 kHz", None),
      ("fallback", "Bandgap fallback (BG_PD = 1, 1.5 V on ua[1])", None), ("mode1", "External SAR (MODE = 1)", "cmp")]
fig, ax = plt.subplots(len(SC), 1, figsize=(11, 3.0 * len(SC)))
for a, (n, title, extra) in zip(ax, SC):
    a2 = a.twinx() if extra else None
    for dut in ("sch", "rc"):
        d = load(f"scen_{n}_{dut}.dat")
        if d is None:
            continue
        t = d[:, 0] * 1e6
        a.plot(t, code(d, 7), **STYLE[dut])
        if extra == "pin1":
            a2.plot(t, d[:, 5], color=STYLE[dut]["color"], lw=0.7, alpha=0.5)
        if extra == "cmp":
            a2.plot(t, d[:, 6], color=STYLE[dut]["color"], lw=0.7, alpha=0.5)
    a.set(title=title, ylabel="D[7:0]")
    if extra == "pin1":
        a2.set_ylabel("ua[1] [V] (thin)"); a2.set_ylim(1.15, 1.22)
    if extra == "cmp":
        a2.set_ylabel("CMP_OUT [V] (thin)")
    a.grid(alpha=0.3); a.legend(fontsize=8, loc="upper left")
ax[-1].set_xlabel("t [µs]")
fig.tight_layout(); fig.savefig(os.path.join(H, "plots", "scenarios.png"), dpi=80)
print("wrote plots/conversions.png, plots/scenarios.png")
