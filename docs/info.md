<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

> **Draft (2026-11-07)** — written while the blocks are verified at the typical corner. Numbers are
> simulation results (tt, 27 °C, 1.8 V) and will be updated after corner/Monte Carlo checks and layout.

## How it works

An 8-bit successive-approximation (SAR) ADC that uses its **own on-chip bandgap reference**, plus an
**on-chip temperature sensor** read through the same ADC.

- **Bandgap reference:** a PNP 1:8 op-amp bandgap gives VBG ≈ 1.215 V (≈ 22 ppm/°C at tt). An RC filter
  and a unity-gain buffer turn it into the ADC reference VREF.
- **Temperature sensor:** a copy of the bandgap's PTAT current into a matched resistor gives
  VPTAT ≈ 0.60 V at 27 °C, rising ≈ 2.0 mV/°C (≈ 2.4 °C per ADC code).
- **ADC:** a 256-unit MIM capacitor DAC (bottom-plate sampling), a StrongARM comparator and synthesized
  SAR logic. A conversion takes 10 clock cycles (1 sample + 8 bits + 1 end-of-conversion), so
  100 kS/s at a 1 MHz clock. LSB = VREF / 256 ≈ 4.75 mV.
- **Input multiplexer** (INSEL): the ADC can convert the external input `ua[0]`, VPTAT, VBG or ground.
- **Reference select** (REF_SEL): internal bandgap reference, or an external reference on `ua[1]`.
  With an external reference, the ADC can measure the internal bandgap voltage itself.
- **External (debug) mode** (MODE = 1): the RP2040 drives the DAC code, sampling and comparator clock
  directly and reads the comparator, so the analog core can be measured even if the SAR logic fails.

## Pins

| Pin | Internal mode (MODE = 0) | External mode (MODE = 1) |
|---|---|---|
| `ua[0]` | VIN, ADC input (0 … VREF) | VIN |
| `ua[1]` | REF_SEL = 1: external VREF input (1.0–1.8 V). REF_SEL = 0 and VREF_OE = 1: buffered VREF output | same |
| `clk` | ADC clock (1 MHz for VIN; **≤ 100 kHz for INSEL = VPTAT or VBG**) | unused |
| `rst_n` | reset (active low) | reset |
| `ui[0]` | START: high = convert continuously | EXT_D0 |
| `ui[1]` | VREF_OE: buffered VREF on `ua[1]` | EXT_D1 |
| `ui[2]` | — | EXT_D2 |
| `ui[3]` | BG_PD: power down bandgap + VREF buffer | EXT_D3 |
| `ui[7:4]` | — | EXT_D[7:4] |
| `uo[7:0]` | D[7:0], conversion result | mirrors EXT_D[7:0] |
| `uio[0]` (in) | MODE | MODE |
| `uio[1]` (in) | — | EXT_SAMPLE (1 = track, 0 = hold) |
| `uio[2]` (in) | — | EXT_CMP_CLK (comparator evaluates while high) |
| `uio[3]` (in) | REF_SEL (0 = internal, 1 = `ua[1]`) | REF_SEL |
| `uio[4]` (out) | CMP_OUT, comparator output | CMP_OUT |
| `uio[5]` (out) | EOC, end of conversion | 0 |
| `uio[7:6]` (in) | INSEL: 00 VIN, 01 VPTAT, 10 VBG, 11 GND | INSEL |

## How to test

All tests run from the TT demo board's RP2040 (MicroPython). Set `uio[0,1,2,3,6,7]` as RP2040
outputs and `uio[4,5]` as inputs. **After power-up (or BG_PD 1 → 0), wait ≥ 100 µs** before the first
conversion: the filtered reference settles in ≈ 45 µs (simulated).

1. **Basic conversion (internal reference).** MODE = 0, REF_SEL = 0, INSEL = 00, clock 1 MHz,
   pulse `rst_n` low, then set START = 1. Apply a DC voltage (0 … 1.2 V) to `ua[0]` from a low-impedance
   source. On each rising edge of EOC, read D[7:0]. Expect D ≈ 256 · VIN / VREF with VREF ≈ 1.21 V.
2. **Reference check and calibration.** Set VREF_OE = 1 and measure `ua[1]` with a ≥ 10 MΩ multimeter:
   ≈ 1.21 V (simulated chip-to-chip spread σ ≈ 18 mV from mismatch, ±0.4 % over process). Store the
   measured value and use it as VREF in all conversions: D · VREF_measured / 256.
   (A 1 MΩ probe reads ≈ 17 mV low, because the buffer's output resistance is ≈ 12 kΩ. Conversions are
   not affected.)
3. **Linearity.** Sweep VIN slowly over 0 … 1.2 V (or use a sine from a function generator) and record
   codes. Compute DNL/INL from the code histogram, ENOB from an FFT.
4. **Temperature sensor.** INSEL = 01, **clock ≤ 100 kHz** (VPTAT has ≈ 270 kΩ source impedance and
   needs a ≥ 4 µs sample phase). About 2.4 °C per code.
   - 1-point calibration: read D0 at a known temperature T0 (°C), then T(°C) = (D / D0) · (T0 + 273.15) − 273.15.
     Simulated: within ±5 °C for most chips, but mismatch can make up to ~10 % of chips worse.
   - 2-point calibration (recommended): read D1 at T1 and D2 at T2 (e.g. room temperature and a hot plate at
     85 °C), then T = T1 + (D − D1) · (T2 − T1) / (D2 − D1). Simulated: within ±2.7 °C (−40…125 °C),
     plus the ±1.2 °C quantization.
5. **Bandgap voltage through the ADC.** Apply a known reference (e.g. 1.500 V) to `ua[1]`, decoupled with
   ≥ 100 nF next to the pin. REF_SEL = 1, INSEL = 10, clock ≤ 100 kHz. VBG = D · VREF_ext / 256.
6. **Fallback: external reference.** If the bandgap doesn't work, REF_SEL = 1 with an external
   reference on `ua[1]` still runs the ADC (tests 1 and 3).
7. **Fallback: external SAR mode.** MODE = 1. Drive EXT_SAMPLE = 1, then 0 (sample), then for each bit
   from MSB to LSB: set the trial code on EXT_D, pulse EXT_CMP_CLK high, read CMP_OUT
   (1 = input below the trial level → clear that bit). This exercises the DAC and comparator without the
   on-chip SAR logic.
8. **Offset check.** INSEL = 11 (ground) should give code 0.

## External hardware

- A DC source or function generator for `ua[0]` (0 … 1.2 V, low output impedance).
- Optional: a precision reference (1.0–1.8 V) and a ≥ 100 nF capacitor on `ua[1]` for tests 5 and 6.
- A ≥ 10 MΩ multimeter for test 2.
