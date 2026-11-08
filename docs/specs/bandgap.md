# Bandgap reference — specification

**Status: DRAFT v0.2** (1x2 tile, 2 analog pins)

## Function

This block generates a temperature-stable voltage `vbg`. The ADC uses it as its reference
(through the VREF buffer). The buffered VREF can be viewed on `ua[1]`. VBG and VPTAT themselves are
measured only through the ADC, never on a pad. It also
provides `vptat`, a PTAT voltage that the ADC digitizes to make the **on-chip temperature sensor**.

## Proposed architecture

- Classic op-amp-based bandgap: two PNP branches with an area ratio of 1:8, using
  `sky130_fd_pr__pnp_05v5_W3p40L3p40` in a 3×3 common-centroid array (1 centre + 8 around).
- High-resistance poly resistors (`sky130_fd_pr__res_xhigh_po_0p35`) to keep the area small at low current.
- Error amplifier: the stage 2 two-stage OTA (a 5-transistor OTA has too little gain).
  Its input offset is amplified onto VBG by about 1 + R2/R1.
- Startup circuit: required. It must release once the core is biased.
- **PTAT branch:** a separate mirrored copy of the PTAT core current into its own resistor
  (not a tap on the core), so the ADC input mux doesn't load the core. Target
  VPTAT ≈ 0.6 V at 27 °C with a slope of ≈ 2 mV/°C, within the ADC range for VREF = 1.215 V.
- **RC low-pass filter** (≈ 1 MΩ + ≈ 4 pF) between `vbg` and the VREF buffer input, decided 2026-11-07,
  for PSRR at 1 MHz and noise. Part of stage 5.
- Power-down input `bg_pd` (`ui[3]`).
- Alternative if 1.62 V headroom is a problem in Phase 2: a current-mode (Banba)
  bandgap with an output of about 0.6–0.9 V. Decide after Phase 1.

## Specification

B1 history: 1.20 V → 1.25 V (2026-11-01, stage 0 ideal-PNP estimate) → **1.215 V** (2026-11-07,
stage 3: the zero-TC point of the real circuit, including the resistor TC, is 1.2154 V at tt;
`sim/bandgap/README.md`). The ±3 % window matches B6.

| # | Parameter | Condition | Min | Typ | Max | Unit | Phase |
|---|---|---|---|---|---|---|---|
| B1 | Output voltage VBG | tt, 27 °C, 1.8 V | 1.18 | 1.215 | 1.25 | V | 1 |
| B2 | Supply current | tt, 27 °C, 1.8 V, enabled | | 20 | 50 | µA | 1 |
| B3 | Startup time (VBG within 1 % of final value) | VDPWR ramp 0→1.8 V in 1 µs | | | 20 | µs | 1 |
| B4 | Line regulation | VDPWR 1.62–1.98 V | | | 10 | mV/V | 2 |
| B5 | Temperature coefficient | −40 … 125 °C, tt | | 30 | 50 | ppm/°C | 2 |
| B6 | VBG spread | all corners, untrimmed | | | ±3 | % | 2 |
| B7 | PSRR (at the filtered VREF buffer input, `vbg_f`) | DC / 1 MHz | 40 / 20 | | | dB | 2 |
| B8 | Power-down current | `bg_pd` = 1 | | | 1 | µA | 2 |
| B9 | Area (core + PTAT branch + startup + VREF buffer) | layout | | | 9 500 | µm² | layout |
| B10 | VPTAT | tt, 27 °C, 1.8 V | 0.5 | 0.6 | 0.7 | V | 1 |
| B11 | VPTAT slope | −40 … 125 °C | 1.8 | 2.0 | | mV/°C | 2 |
| B12 | Temperature-sensor resolution (via 8-bit ADC, VREF = 1.215 V) | | | 2.4 | 2.7 | °C/LSB | 2 |
| B13 | Temperature-sensor accuracy, untrimmed (1-point calibration in firmware) | −40 … 125 °C | | ±3 | ±5 | °C | 2 |

## Testbenches (to be written in `sim/bandgap/`)

| TB | Measures | Analysis |
|---|---|---|
| `tb_bg_op` | B1, B2 | `.op` |
| `tb_bg_startup` | B3 (also: proves the circuit doesn't stay in the zero-current state) | `.tran`, supply ramp |
| `tb_bg_line` | B4 | `.dc` sweep of VDPWR |
| `tb_bg_temp` | B5 | `.dc temp` sweep |
| `tb_bg_psrr` | B7 | `.ac` with AC source on VDPWR |
| `tb_bg_ptat` | B10, B11 | `.op` and `.dc temp` on `vptat` |

## Status

| # | Result | Phase | Date | Notes |
|---|---|---|---|---|
| B1 | 1.2105 V | 1 (tt) | 2026-11-08 | ✅ after the Phase 2 resize (was 1.2154 V); corners 1.2059–1.2146 V |
| B2 | 15.7 µA (incl. bias_gen) | 1 | 2026-11-08 | core 13.6 µA; unchanged by the resize |
| B3 | 2.4 µs after a 1 µs ramp (tt); 63/63 corner runs start on both ramps | 2 | 2026-11-08 | startup MSU1 0.42/1 → 0.42/4 fixed a limit cycle caused by the resize |
| B4 | 2.2 mV/V (tt); worst 9.88 mV/V (fs, 125 °C) | 2 | 2026-11-08 | ✅ but marginal at fs/125 °C |
| B5 | 23.5 ppm/°C (tt); worst corner 33.3 ppm/°C (ff) | 2 | 2026-11-08 | ✅ |
| B7 | tt: 55.7 dB DC / 22.2 dB at 1 MHz at `vbg_f`. Corners: 1 MHz ≥ 20.3 dB ✅; DC ≥ 30.4 dB (40 dB not met in 7 of 45 runs, all at 1.62 V and −40/125 °C) | 2 | 2026-11-08 | filter grown to 1.6 MΩ / 5.5 pF; **open: see the B7 note** |
| B8 | 0.08 nA (tt) | early, tt only | 2026-11-08 | incl. bias_gen |
| B10 | 0.6005 V | 1 | 2026-11-08 | stage 4, after the resize |
| B11 | 1.956 mV/°C | early, tt only | 2026-11-08 | |
| B12 | 2.43 °C/LSB | early, tt only | 2026-11-08 | LSB = 4.75 mV |
| B13 | corners ≤ 2.6 °C (1-point cal.); mismatch: 10 % of seeds > 5 °C with 1 point, ≤ 2.7 °C with 2 points | 2 | 2026-11-08 | **open: see the B13 note**; `sim/ptat/sensor.md`; ADC quantization (±1.2 °C) not included |
| B6 | corners: −0.4 / +0.3 % (63 runs) ✅. Mismatch: σ = 17.6 mV (1.45 %, Monte Carlo 100 seeds) | 2 | 2026-11-08 | **open: see the B6 note below** |

## B6 note — VBG spread with mismatch (open, for the designer, 2026-11-08)

Corners alone give −0.4 / +0.3 % (B6 passes easily). Mismatch adds **σ(VBG) = 17.6 mV** (Monte Carlo, tt, 100 seeds),
so the 3σ untrimmed spread is ±53 mV ≈ ±4.4 %, which is above ±3 %. This is already 3× better than the first
sizing (54 mV). The largest remaining part is the OTA offset, multiplied by 1 + R2/R1 ≈ 10.5 (`sim/bandgap/README.md`).
Options:
1. **Accept and reword B6**: corners ±3 % (met) and mismatch σ ≤ 20 mV (met). Rely on the built-in
   calibration path: VREF is measured on `ua[1]` with a DMM (VREF_OE = 1), and firmware scales the ADC codes.
   No area cost. *Recommended.*
2. Larger PNP ratio (1 : 24, a 5 × 5 array): R2/R1 drops from 9.5 to about 6, so the OTA and resistor parts drop by
   about 35 %, to σ ≈ 12–13 mV. Cost: about +400 µm² and another layout iteration of `pnp_array`.
3. Chopping the OTA: largest gain, but it needs a clock, switches and a filter. Too big a change this late.

## B13 note — temperature-sensor accuracy (open, for the designer, 2026-11-08)

The corners alone give ≤ 2.6 °C after a 1-point calibration at 27 °C. Mismatch changes the slope of VPTAT/VBG
(σ 1.6 %), so with 1 point, 10 % of chips exceed ±5 °C (95th percentile 5.4 °C). A second calibration point
(e.g. 85 °C on a hot plate, or any second known temperature) brings every seed within 2.7 °C.
Recommendation: keep the circuit, make the test procedure a 2-point calibration, and reword B13 to
"±3 °C after a 2-point calibration; ±5 °C typical after 1 point".

## B7 note — DC PSRR at the minimum supply (open, for the designer, 2026-11-08)

The 1 MHz part of B7 passes in every corner (≥ 20.3 dB). DC PSRR is ≥ 40 dB except at 1.62 V with −40 °C or
125 °C, where it is 30–37 dB (7 of 45 runs). The cause is headroom at 1.62 V (`sim/vref/corners.md`). Two cheap
resizes didn't fix it. Effect: 0.3 mV of VREF change for 10 mV of supply ripple (0.07 LSB). B4 passes everywhere.
Recommendation: reword B7 DC to "≥ 40 dB at 1.8 V, ≥ 30 dB at 1.62 V over temperature" and keep the circuit.
The real fix is cascoded PMOS sources, which need a higher supply, so it isn't possible with VDPWR only.
