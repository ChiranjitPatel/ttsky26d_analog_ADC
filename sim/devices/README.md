# Stage 0 — device sanity

`./run.sh` runs `tb_mos`, `tb_pnp`, `tb_res`, `tb_mim` (tt, 27 °C) and writes `results.md`,
the gm/Id lookup tables in `lut/` and the plots in `plots/`.

## Findings (2026-11-01, Phase 1)

1. **Zero-TC bandgap voltage is ≈ 1.25 V, not 1.20 V.** With this PNP (ideality 1.012,
   CTAT −1.92 mV/K at 1 µA), the first-order zero-TC point is VBG ≈ 1253 mV. That's above spec B1's
   1.24 V maximum. Proposal: move B1 to 1.25 V typ (1.21–1.29 V); the ADC LSB becomes 4.88 mV.
2. **Headroom is tight.** 1.25 V at VDPWR = 1.62 V leaves ≈ 0.37 V for the PMOS current sources,
   and Vbe rises to ≈ 0.80 V at −40 °C. This must be checked first in stage 3 Phase 2; the
   current-mode (Banba) fallback in `docs/specs/bandgap.md` stays open.
3. **The PTAT branch works as planned.** A gain of 11.0 on ΔVbe gives VPTAT = 0.6 V at 27 °C and
   2.01 mV/°C (spec B11 ≥ 1.8 mV/°C).
4. **`res_xhigh_po` has a large TC1 (−1470 ppm/K).** Ratios within one resistor type cancel it,
   so the core and PTAT resistors must be the same type (and matched in layout).
   `res_high_po_0p35` at 386 Ω/□ is higher than the wide-resistor value because of the narrow width.
5. **MIM unit cap is 9.30 fF** (2.000 fF/µm² + 0.164 fF/µm perimeter), matching the 9–10 fF
   assumed in spec A-series. The full DAC is 2.38 pF.
6. **Avoid L = 0.15 µm for analog devices.** Intrinsic gain is only ~10–20 there. sky130 models are
   binned, which shows up as non-monotonic steps between lengths (for example `nfet_01v8_lvt`
   L = 1 µm has less gain than L = 0.5 µm). Size from the LUTs at the exact L used, and prefer
   L ≥ 0.5 µm for mirrors and amplifier devices.
7. The `Vth` column is the BSIM `vth` operating-point parameter at |Vds| = 0.9 V, so it includes
   short-channel and binning effects. Use gm/Id for sizing rather than Vth.
