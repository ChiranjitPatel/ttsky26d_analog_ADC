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
- Error amplifier: 5-transistor OTA or a two-stage OTA. Pick whichever has enough gain and
  input-offset tolerance (offset is amplified onto VBG).
- Startup circuit: required. It must release once the core is biased.
- **PTAT branch:** a separate mirrored copy of the PTAT core current into its own resistor
  (not a tap on the core), so the ADC input mux doesn't load the core. Target
  VPTAT ≈ 0.6 V at 27 °C with a slope of ≈ 2 mV/°C, within the ADC range for VREF = 1.2 V.
- Power-down input `bg_pd` (`ui[3]`).
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
| B8 | Power-down current | `bg_pd` = 1 | | | 1 | µA | 2 |
| B9 | Area (core + PTAT branch + startup + VREF buffer) | layout | | | 9 500 | µm² | layout |
| B10 | VPTAT | tt, 27 °C, 1.8 V | 0.5 | 0.6 | 0.7 | V | 1 |
| B11 | VPTAT slope | −40 … 125 °C | 1.8 | 2.0 | | mV/°C | 2 |
| B12 | Temperature-sensor resolution (via 8-bit ADC, VREF = 1.2 V) | | | 2.3 | 2.6 | °C/LSB | 2 |
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
| — | not yet simulated | | | |
