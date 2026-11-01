# 8-bit SAR ADC — specification

**Status: DRAFT v0.2** (1x2 tile, 2 analog pins)

## Function

The ADC samples the output of the input mux (`INSEL`: VIN on `ua[0]`, VPTAT, VBG or VGND) and
converts it to an 8-bit code `D[7:0]` on `uo[7:0]` in 10 clock cycles (1 sample + 8 bit
decisions + 1 EOC). It runs in two modes:

- **Internal mode** (`MODE` = 0): the on-chip SAR logic performs the conversion and raises `EOC` when done.
- **External mode** (`MODE` = 1): the RP2040 drives the DAC code, sample and comparator
  clock directly and reads `CMP_OUT`. This is the fallback and debug path.

## Proposed architecture

- **Topology:** single-ended charge-redistribution SAR, binary-weighted cap DAC
  (128C … 1C + 1C termination = 256 C_u), bottom-plate sampling, conventional switching.
  Single-ended keeps the first version simple. A differential version is a possible upgrade later.
- **Unit capacitor C_u:** MIM `sky130_fd_pr__cap_mim_m3_1`, 2 × 2 µm (≈ 9–10 fF including fringe).
  Total DAC capacitance is about 2.5 pF. 16 × 16 common-centroid array with a ring of dummies,
  ≈ 70 × 70 µm. MIM is proven on TT (TT06 silicon, see `prior_art.md`).
- **Input mux:** transmission gates selecting VIN / VPTAT / VBG / VGND ahead of the sampling switch.
- **Sampling switch:** bootstrapped switch not needed at 100 kS/s for 8 bits. Use a CMOS
  transmission gate, sized for settling (see A9).
- **Comparator:** StrongARM latch followed by an SR latch. Kickback onto the DAC top plate must be
  checked in simulation (TT06 silicon showed harmonics attributed to kickback/interference); add
  a preamp only if needed and if area allows. Shield the top-plate routing.
- **SAR logic:** 8-bit successive-approximation register plus a sequencer, built from
  sky130_fd_sc_hd standard cells (implementation method TBD).
- **Reference:** `vref` = buffered bandgap (≈ 1.2 V) or external VREF on `ua[1]` (1.0–1.8 V), selected by `REF_SEL`.

## Specification

LSB = VREF / 256 ≈ 4.69 mV at VREF = 1.2 V.

| # | Parameter | Condition | Min | Typ | Max | Unit | Phase |
|---|---|---|---|---|---|---|---|
| A1 | Resolution | | | 8 | | bit | — |
| A2 | Input range | | 0 | | VREF | V | 1 |
| A3 | Sample rate | `clk` = 1 MHz, 10 clocks/conversion | | 100 | | kS/s | 1 |
| A4 | DNL | ramp, tt 27 °C | −0.5 | | +0.5 | LSB | 1 |
| A5 | INL | ramp, tt 27 °C | −1 | | +1 | LSB | 1 |
| A6 | ENOB | sine near Nyquist, tt 27 °C | 7.0 | 7.5 | | bit | 1 |
| A7 | Comparator input offset (σ) | Monte Carlo | | | 10 | mV | 2 |
| A8 | Comparator input-referred noise | | | | 1.2 (LSB/4) | mV rms | 2 |
| A9 | Sampling settling error | including pad R + switch | | | 0.5 | LSB | 1 |
| A10 | Comparator decision time | 1 mV overdrive | | | 50 | ns | 1 |
| A11 | Supply current (ADC + VREF buffer) | converting, 1 MHz | | 150 | 300 | µA | 1 |
| A12 | Max clock (stretch) | tt 27 °C | 10 | | | MHz | 2 |
| A13 | Cap DAC mismatch-induced DNL (σ) | Monte Carlo on C_u | | | 0.25 | LSB | 2 |
| A14 | Input-mux crosstalk (unselected → selected input) | DC | | | 0.25 | LSB | 1 |
| A15 | Area (DAC + comparator + switch + SAR logic) | layout | | | 10 500 | µm² | layout |

Offset (A7) only shifts the transfer curve; it doesn't affect DNL. That's why the limit is
loose compared to the LSB.

## Testbenches (to be written in `sim/sar_adc/`)

| TB | Measures | Analysis |
|---|---|---|
| `tb_cmp` | A10, comparator function | `.tran` with clocked comparator |
| `tb_cmp_mc` | A7 | Monte Carlo `.tran` / bisection |
| `tb_sample` | A9 | `.tran`, step on VIN through a pad model |
| `tb_dac` | DAC linearity, A13 | `.tran` / `.op` stepping codes |
| `tb_adc_ramp` | A2, A4, A5 | full ADC `.tran` with slow ramp, codes histogram |
| `tb_adc_sine` | A6 | full ADC `.tran`, FFT of reconstructed output |
| `tb_adc_power` | A11 | `.tran`, average supply current |
| `tb_inmux` | A14 | `.op` / `.tran`, each `INSEL` setting |

## Status

| # | Result | Phase | Date | Notes |
|---|---|---|---|---|
| — | not yet simulated | | | |
