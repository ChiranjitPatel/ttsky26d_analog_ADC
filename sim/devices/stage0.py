#!/usr/bin/env python3
"""Stage 0 post-processing: device sanity numbers, gm/Id lookup tables, plots.

Run the testbenches first (see run.sh). Reads ../out/devices/*.dat, writes:
  lut/<device>.csv     gm/Id lookup tables (W = 2 um, |Vds| = 0.9 V, tt, 27 C)
  plots/*.png          characterization plots
  results.md           summary used to fill the Status table in docs/specs/stage_plan.md
"""
import math
import os
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out", "devices")
os.makedirs(os.path.join(HERE, "lut"), exist_ok=True)
os.makedirs(os.path.join(HERE, "plots"), exist_ok=True)

K_B, Q_E = 1.380649e-23, 1.602176634e-19
W_MOS = 2.0  # um, all MOS testbench devices


def load(name):
    path = os.path.join(OUT, name)
    with open(path) as f:
        header = f.readline().lower().split()
    return header, np.loadtxt(path, skiprows=1)


# ---------------------------------------------------------------- MOSFETs
hdr, d = load("mos.dat")
vgs = d[:, hdr.index("v(gn)")]
pat = re.compile(r"@m\.x(\w+?)_(\d+p?\d*)\.msky130_fd_pr__(\w+)\[(\w+)\]")
devs = {}
for i, h in enumerate(hdr):
    m = pat.fullmatch(h)
    if m:
        _, lstr, model, q = m.groups()
        L = float(lstr.replace("p", "."))
        devs.setdefault(model, {}).setdefault(L, {})[q] = np.abs(d[:, i])

mos_rows = []
for model, byL in devs.items():
    lut = ["L_um,vgs_V,id_per_w_A_per_um,gm_over_id_per_V,gm_over_gds,ft_Hz,vth_V"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for L, q in sorted(byL.items()):
        idw = q["id"] / W_MOS
        ok = q["id"] > 1e-12
        gmid = np.where(ok, q["gm"] / np.maximum(q["id"], 1e-30), np.nan)
        gain = np.where(q["gds"] > 0, q["gm"] / np.maximum(q["gds"], 1e-30), np.nan)
        ft = q["gm"] / (2 * math.pi * np.maximum(q["cgg"], 1e-30))
        for k in range(len(vgs)):
            if ok[k]:
                lut.append(f"{L},{vgs[k]:.3f},{idw[k]:.4e},{gmid[k]:.3f},{gain[k]:.2f},{ft[k]:.3e},{q['vth'][k]:.4f}")
        ax[0].semilogx(idw[ok], gmid[ok], label=f"L={L}")
        ax[1].plot(gmid[ok], gain[ok], label=f"L={L}")
        # summary values: Vth at |Vgs| = 0.9 V; Id/W and gm/gds at gm/Id = 10 and 15 (strong / moderate inversion)
        k09 = int(np.argmin(abs(vgs - 0.9)))
        row = {"model": model, "L": L, "vth": q["vth"][k09]}
        for target in (10, 15):
            sel = np.where(ok & (vgs > 0.2))[0]
            j = sel[int(np.nanargmin(abs(gmid[sel] - target)))]
            row[f"idw{target}"], row[f"gain{target}"] = idw[j], gain[j]
        mos_rows.append(row)
    ax[0].set(xlabel="Id/W [A/um]", ylabel="gm/Id [1/V]", title=f"{model}: gm/Id vs current density")
    ax[1].set(xlabel="gm/Id [1/V]", ylabel="gm/gds", title=f"{model}: intrinsic gain")
    for a in ax:
        a.grid(True, which="both", alpha=0.3)
        a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "plots", f"{model}.png"), dpi=90)
    plt.close(fig)
    with open(os.path.join(HERE, "lut", f"{model}.csv"), "w") as f:
        f.write("\n".join(lut) + "\n")

# ---------------------------------------------------------------- PNP
hdr, d = load("pnp_i.dat")
ie, vbe1, vbe8 = d[:, 0], d[:, hdr.index("v(e1)")], d[:, hdr.index("v(e8)")]
k1u = int(np.argmin(abs(ie - 1e-6)))
hdr, d = load("pnp_t.dat")
tC, vt1, vt8 = d[:, 0], d[:, hdr.index("v(e1)")], d[:, hdr.index("v(e8)")]
dvbe = vt1 - vt8
k27 = int(np.argmin(abs(tC - 27)))
dvbe_dT = np.gradient(vt1, tC)[k27]          # V/K, CTAT slope
ddvbe_dT = np.gradient(dvbe, tC)[k27]        # V/K, PTAT slope
VT27 = K_B * (27 + 273.15) / Q_E
n_ideal = dvbe[k27] / (VT27 * math.log(8))
# First-order bandgap: VBG = Vbe1 + K * dVbe, with dVBG/dT = 0 at 27 C
K_bg = -dvbe_dT / ddvbe_dT
vbg_T = vt1 + K_bg * dvbe
vbg27 = vbg_T[k27]
vbg_spread = vbg_T.max() - vbg_T.min()
tc_ppm = vbg_spread / vbg27 / (tC[-1] - tC[0]) * 1e6
# PTAT output for the temperature sensor: VPTAT = K_ptat * dVbe, chosen so VPTAT(27 C) = 0.6 V
K_ptat = 0.6 / dvbe[k27]
ptat_slope = K_ptat * ddvbe_dT

fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
ax[0].semilogx(ie, vbe1, label="1 x PNP")
ax[0].semilogx(ie, vbe8, label="8 x PNP")
ax[0].set(xlabel="Ie [A]", ylabel="Vbe [V]", title="Vbe vs current (27 C)")
ax[1].plot(tC, vt1 * 1e3, label="Vbe (1 uA)")
ax[1].plot(tC, dvbe * 1e3 * 10, label="10 x dVbe")
ax[1].set(xlabel="T [C]", ylabel="mV", title="CTAT and PTAT (1 uA)")
ax[2].plot(tC, vbg_T * 1e3)
ax[2].set(xlabel="T [C]", ylabel="VBG [mV]", title=f"Ideal first-order VBG, K = {K_bg:.2f}")
for a in ax:
    a.grid(True, which="both", alpha=0.3)
    a.legend(fontsize=7) if a.get_legend_handles_labels()[0] else None
fig.tight_layout()
fig.savefig(os.path.join(HERE, "plots", "pnp.png"), dpi=90)
plt.close(fig)

# ---------------------------------------------------------------- resistors
hdr, d = load("res.dat")
tR = d[:, 0]
kR = int(np.argmin(abs(tR - 27)))
res = {}
for name, cs, cl in (("res_xhigh_po_0p35", "i(vxs)", "i(vxl)"), ("res_high_po_0p35", "i(vhs)", "i(vhl)")):
    rs = 1.0 / np.abs(d[:, hdr.index(cs)])
    rl = 1.0 / np.abs(d[:, hdr.index(cl)])
    rsh = (rl - rs) / ((20 - 5) / 0.35)          # ohm/sq
    rend = (rs - rsh * 5 / 0.35) / 2             # ohm per end
    tc1 = np.gradient(rl, tR)[kR] / rl[kR] * 1e6  # ppm/K of the 20 um resistor
    res[name] = dict(rsh=rsh[kR], rend=rend[kR], tc1=tc1, r20=rl[kR])

# ---------------------------------------------------------------- MIM
hdr, d = load("mim.dat")
row = np.atleast_2d(d)[0]
c = {s: row[hdr.index(f"c{s}")] for s in (2, 5, 10)}
# Fit C = Ca*A + Cp*P using the 5 and 10 um caps, check against 2 um
A = np.array([[25, 20], [100, 40]])
Ca, Cp = np.linalg.solve(A, [c[5], c[10]])
c2_fit = Ca * 4 + Cp * 8

# ---------------------------------------------------------------- report
L = ["# Stage 0 — device sanity results", "",
     "tt corner, 27 °C, generated by `stage0.py` from `tb_mos/pnp/res/mim.spice`.", "",
     "## MOSFETs (W = 2 µm, |Vds| = 0.9 V)", "",
     "| Device | L (µm) | Vth @ \\|Vgs\\|=0.9 V (V) | Id/W @ gm/Id=10 (µA/µm) | gm/gds @ gm/Id=10 | Id/W @ gm/Id=15 (µA/µm) | gm/gds @ gm/Id=15 |",
     "|---|---|---|---|---|---|---|"]
for r in mos_rows:
    L.append(f"| `{r['model']}` | {r['L']} | {r['vth']:.3f} | {r['idw10']*1e6:.2f} | {r['gain10']:.0f} | {r['idw15']*1e6:.3f} | {r['gain15']:.0f} |")
L += ["", "Full tables: `lut/<device>.csv`. Plots: `plots/<device>.png`.", "",
      "## PNP `pnp_05v5_W3p40L3p40` (diode-connected)", "",
      "| Quantity | Value |", "|---|---|",
      f"| Vbe @ 1 µA, 27 °C | {vbe1[k1u]*1e3:.1f} mV |",
      f"| dVbe/dT @ 1 µA (CTAT) | {dvbe_dT*1e3:.3f} mV/K |",
      f"| ΔVbe (1 vs 8 devices, same current) @ 27 °C | {dvbe[k27]*1e3:.2f} mV (ideal kT/q·ln8 = {VT27*math.log(8)*1e3:.2f} mV) |",
      f"| Effective ideality n | {n_ideal:.4f} |",
      f"| dΔVbe/dT (PTAT) | {ddvbe_dT*1e6:.1f} µV/K |", "",
      "### What this means for the bandgap (first-order, ideal amplifier)", "",
      f"- Zero-TC gain on ΔVbe: **K = {K_bg:.2f}** (VBG = Vbe + K·ΔVbe). The resistor ratio that sets K depends on the core topology chosen in stage 3.",
      f"- Predicted VBG @ 27 °C: **{vbg27*1e3:.0f} mV**. Curvature over −40…125 °C: {vbg_spread*1e3:.1f} mV ≈ **{tc_ppm:.0f} ppm/°C** (box method) — inside spec B5 (≤ 50 ppm/°C).",
      f"- PTAT output for VPTAT(27 °C) = 0.6 V needs gain {K_ptat:.2f} on ΔVbe → slope **{ptat_slope*1e3:.2f} mV/°C** (spec B11 ≥ 1.8 mV/°C).", "",
      "## Poly resistors (W = 0.35 µm)", "",
      "| Device | Sheet R (Ω/□) | End R (Ω) | R(L=20 µm) (kΩ) | TC1 (ppm/K) |", "|---|---|---|---|---|"]
for k, v in res.items():
    L.append(f"| `{k}` | {v['rsh']:.0f} | {v['rend']:.0f} | {v['r20']/1e3:.1f} | {v['tc1']:.0f} |")
L += ["", "## MIM capacitor `cap_mim_m3_1`", "",
      "| Quantity | Value |", "|---|---|",
      f"| C(2 × 2 µm) — DAC unit cap | **{c[2]*1e15:.2f} fF** |",
      f"| C(5 × 5 µm) | {c[5]*1e15:.2f} fF |",
      f"| C(10 × 10 µm) | {c[10]*1e15:.2f} fF |",
      f"| Area term Ca | {Ca*1e15:.3f} fF/µm² |",
      f"| Perimeter term Cp | {Cp*1e15:.3f} fF/µm |",
      f"| 2 × 2 µm from fit (check) | {c2_fit*1e15:.2f} fF |",
      f"| 256-unit DAC total | {256*c[2]*1e12:.2f} pF |", ""]
with open(os.path.join(HERE, "results.md"), "w") as f:
    f.write("\n".join(L))
print("\n".join(L))
