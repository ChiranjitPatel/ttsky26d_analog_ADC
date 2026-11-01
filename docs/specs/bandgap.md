# Bandgap reference — specification

**Status: DRAFT v0.1**

## Function

This block generates a temperature-stable voltage `vbg`. The ADC uses it as its reference
(through the VREF buffer), and it can be viewed on `ua[1]` through the debug mux. It also
provides a PTAT voltage for temperature monitoring.

## Proposed architecture

- Classic op-amp-based bandgap: two PNP branches with an area ratio of 1:8, using
  `sky130_fd_pr__pnp_05v5_W3p40L3p40` in a 3×3 common-centroid array (1 centre + 8 around).
- High-resistance poly resistors (`sky130_fd_pr__res_xhigh_po_0p35`) to keep the area small at low current.
- Error amplifier: 5-transistor OTA or a two-stage OTA. Pick whichever has enough gain and
  input-offset tolerance (offset is amplified onto VBG).
- Startup circuit: required. It must release once the core is biased.
- Enable / power-down input `en_bg`.
- Alternative if 1.62 V headroom is a problem in Phase 2: a current-mode (Banba)
  bandgap with an output of about 0.6–0.9 V. Decide after Phase 1.

## Specification

| # | Parameter | Condition | Min | Typ | Max | Unit | Phase |
|---|---|---|---|---|---|---|---|
| B1 | Output voltage VBG | tt, 27 °C, 1.8 V | 1.16 | 1.20 | 1.24 | V | 1 |
| B2 | Supply current | tt, 27 °C, 1.8 V, enabled | | 20 | 50 | µA | 1 |
| B3 | Startup time (VBG within 1 % of final value) | VDPWR ramp 0→1.8 V in 1 µs | | | 20 | µs | 1 |
| B4 | Line regulation | VDPWR 1.62–1.98 V | | | 10 | mV/V | 2 |
| B5 | Temperature coefficient | −40 … 125 °C, tt | | 30 | 50 | ppm/°C | 2 |
| B6 | VBG spread | all corners, untrimmed | | | ±3 | % | 2 |
| B7 | PSRR | DC / 1 MHz | 40 / 20 | | | dB | 2 |
| B8 | Power-down current | `en_bg` = 0 | | | 1 | µA | 2 |
| B9 | Area | | | | 100 × 80 | µm | layout |

## Testbenches (to be written in `sim/bandgap/`)

| TB | Measures | Analysis |
|---|---|---|
| `tb_bg_op` | B1, B2 | `.op` |
| `tb_bg_startup` | B3 (also: proves the circuit doesn't stay in the zero-current state) | `.tran`, supply ramp |
| `tb_bg_line` | B4 | `.dc` sweep of VDPWR |
| `tb_bg_temp` | B5 | `.dc temp` sweep |
| `tb_bg_psrr` | B7 | `.ac` with AC source on VDPWR |

## Status

| # | Result | Phase | Date | Notes |
|---|---|---|---|---|
| — | not yet simulated | | | |
