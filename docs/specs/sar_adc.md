# 8-bit SAR ADC — specification

**Status: DRAFT v0.1**

## Function

The ADC samples `vin` (`ua[0]`) and converts it to an 8-bit code `D[7:0]` on `uo[7:0]` in
9 clock cycles (1 sample + 8 bit decisions). It runs in two modes:

- **Internal mode** (`MODE` = 0): the on-chip SAR logic performs the conversion and raises `EOC` when done.
- **External mode** (`MODE` = 1): the RP2040 drives the DAC code, sample and comparator
  clock directly and reads `CMP_OUT`. This is the fallback and debug path.

## Proposed architecture

- **Topology:** single-ended charge-redistribution SAR, binary-weighted cap DAC
  (128C … 1C + 1C termination = 256 C_u), bottom-plate sampling, conventional switching.
  Single-ended keeps the first version simple. A differential version is a possible upgrade later.
- **Unit capacitor C_u:** target about 10 fF (MIM or MOM, see open question in `top_level.md`).
  Total DAC capacitance is about 2.6 pF. Common-centroid layout with a ring of dummies.
- **Sampling switch:** bootstrapped switch not needed at 100 kS/s for 8 bits. Use a CMOS
  transmission gate, sized for settling (see A9).
- **Comparator:** StrongARM latch with an optional preamp to reduce kickback onto the DAC
  top plate, followed by an SR latch.
- **SAR logic:** 8-bit successive-approximation register plus a sequencer, built from
  sky130_fd_sc_hd standard cells (implementation method TBD).
- **Reference:** `vref` = buffered bandgap (≈ 1.2 V) or `ua[2]`, selected by `REF_SEL`.

## Specification

LSB = VREF / 256 ≈ 4.69 mV at VREF = 1.2 V.

| # | Parameter | Condition | Min | Typ | Max | Unit | Phase |
|---|---|---|---|---|---|---|---|
| A1 | Resolution | | | 8 | | bit | — |
| A2 | Input range | | 0 | | VREF | V | 1 |
| A3 | Sample rate | `clk` = 1 MHz | | 100 | | kS/s | 1 |
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

## Status

| # | Result | Phase | Date | Notes |
|---|---|---|---|---|
| — | not yet simulated | | | |
