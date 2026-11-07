#!/usr/bin/env python3
"""SNDR / ENOB from the 64-point coherent sine (chunks sine_0..sine_3, 16 conversions each).

The same input samples are also quantized by an ideal 8-bit ADC (floor(256*vin/VREF)), because a
64-point record limits the attainable ENOB; the comparison with the ideal quantizer is what counts.
Writes results_sine.md and plots/sine.png.
"""
import os, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

H = os.path.dirname(os.path.abspath(__file__))
O = os.path.join(H, "..", "out", "adc")
N, M, VREF = 64, 7, 1.215
vin, codes = [], []
for c in range(4):
    for line in open(os.path.join(O, f"sine_{c}.codes.txt")):
        m = re.match(r"vin=([-0-9.]+) V .* code=\s*(\d+)", line)
        if m:
            vin.append(float(m.group(1))); codes.append(int(m.group(2)))
vin, codes = np.array(vin), np.array(codes)
assert len(codes) == N, f"expected {N} codes, got {len(codes)}"
ideal = np.clip(np.floor(256 * vin / VREF), 0, 255)

def sndr(x):
    X = np.fft.rfft(x - x.mean()); P = abs(X) ** 2
    sig = P[M]; noise = P[1:].sum() - sig
    s = 10 * np.log10(sig / noise)
    return s, (s - 1.76) / 6.02, P
s_adc, e_adc, P_adc = sndr(codes.astype(float))
s_id, e_id, _ = sndr(ideal)
err = codes - ideal

os.makedirs(os.path.join(H, "plots"), exist_ok=True)
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
ax[0].plot(codes, "o-", ms=3, label="ADC (transistor level)"); ax[0].plot(ideal, "x", ms=4, label="ideal 8-bit")
ax[0].set(xlabel="sample", ylabel="code", title=f"64-point sine, {M} cycles"); ax[0].legend(fontsize=7)
f = np.arange(len(P_adc)); ax[1].stem(f[1:], 10 * np.log10(P_adc[1:] / P_adc[M]), basefmt=" ")
ax[1].set(xlabel="FFT bin", ylabel="dBc", title=f"Spectrum: SNDR {s_adc:.1f} dB, ENOB {e_adc:.2f}")
for a in ax: a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(H, "plots", "sine.png"), dpi=90)
md = ["# I2 — 64-point coherent sine (transistor level, tt, 27 °C, 1.8 V, ideal VREF)", "",
      f"Input: {0.6075:.4f} V ± 0.58 V, {M} cycles in {N} samples (100 kS/s at 1 MHz clock).", "",
      "| Quantity | ADC | Ideal 8-bit quantizer, same samples |", "|---|---|---|",
      f"| SNDR | {s_adc:.2f} dB | {s_id:.2f} dB |", f"| ENOB | {e_adc:.2f} bit | {e_id:.2f} bit |",
      f"| Codes different from the ideal quantizer | {int((err != 0).sum())} of {N} (max {int(abs(err).max())} LSB) | — |",
      "", "![sine](plots/sine.png)", ""]
open(os.path.join(H, "results_sine.md"), "w").write("\n".join(md)); print("\n".join(md))
