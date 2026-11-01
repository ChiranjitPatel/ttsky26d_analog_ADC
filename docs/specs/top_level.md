# Top-level specification — bandgap-referenced 8-bit SAR ADC + temperature sensor

**Status: DRAFT v0.2** — targets a **1x2 tile with 2 analog pins** (already purchased).

## What sets this design apart

Other projects have submitted plain SAR ADCs and stand-alone bandgaps before (see
`prior_art.md`). This design combines them into one small, self-measuring system:

1. An 8-bit SAR ADC that uses its **own on-chip bandgap** as the reference.
2. An **on-chip temperature sensor**: the bandgap's PTAT voltage is digitized by the same ADC.
3. **Self-characterization**: with an external reference applied on `ua[1]`, the ADC measures
   the internal bandgap and PTAT voltages. This gives silicon data for the bandgap without needing extra pins.
4. An **external SAR mode**: the RP2040 can drive the DAC and read the comparator directly, so
   the analog core can be measured even if the SAR logic fails.

## Block diagram

```
                       VDPWR 1.8 V
                           │
  ┌────────────────────────┴──────────────────────────────────────────┐
  │ ┌───────────┐ vbg  ┌──────────┐ vref_int  ┌────────┐               │
  │ │ Bandgap   ├─────►│ VREF buf ├──────────►│ REF    │ vref          │
  │ │ + startup │      └──────────┘           │ select ├────┐          │
  │ │           ├─ vptat (PTAT branch)        └───▲────┘    │          │
  │ └───────────┘                                 │         │          │
  │                                               │         ▼          │
  │ ua[0] VIN ──►┌───────┐ vadc ┌────────┐  ┌──────────┐  ┌─────────┐  │
  │   vptat ────►│ input ├─────►│ 8b cap ├─►│ StrongARM├─►│ SAR     ├──┼─► uo[7:0] D, uio[5] EOC
  │   vbg   ────►│ mux   │      │ DAC+S/H│  │ comp.    │  │ logic   │  │
  │   VGND  ────►└───────┘      └───▲────┘  └────┬─────┘  └────┬────┘  │
  │                                 └────── code ◄──────────────┘      │
  │                                   (or ui[7:0] in external mode)    │
  │ ua[1] ◄──► AMUX out (VBG / VREF / VPTAT)  or  VREF_EXT in ─────────┘
  └────────────────────────────────────────────────────────────────────┘
```

## Global specs

| Parameter | Value |
|---|---|
| Process | sky130 |
| Supply | VDPWR = 1.8 V only (no VAPWR) |
| Tiles | **1x2** = **161.00 × 225.76 µm** (36 347 µm²), from TT `tt-support-tools` `tech/sky130A/tile_sizes.yaml` and `def/analog/tt_analog_1x2.def` |
| Pin locations | `ua[0]` at x = 152.26 µm, `ua[1]` at x = 132.94 µm, on the **bottom** edge (met4, 0.9 × 1.0 µm). Digital pins (`clk`, `ui_in`, …) on the **top** edge (met4, 0.3 × 1.0 µm). Place VIN-side analog near the bottom right and SAR logic near the top |
| Power | We draw our own `VDPWR`/`VGND` straps; they must be on **met4**, at least **1.2 µm** wide (precheck rule) |
| Allowed layers | Full sky130 stack including met5, `capm` (MIM m3–m4) and `capm2` (MIM m4–m5) |
| Analog pins | **2** (`ua[0]`, `ua[1]`) |
| Total supply current | < 300 µA while converting (target), < 10 µA powered down (stretch) |
| Clock | `clk` = SAR clock, 1 MHz nominal (≈ 100 kS/s, 10 clocks/conversion), 10 MHz stretch |

## Area budget (estimates; replace with real numbers after layout)

| Block | Budget (µm²) |
|---|---|
| Cap DAC, 256 × MIM unit + dummies | 5 000 |
| Comparator + sampling switch | 1 500 |
| SAR logic + digital control (standard cells) | 4 000 |
| Bandgap core + PTAT branch + startup | 8 000 |
| VREF buffer, input mux, ua[1] mux | 1 500 |
| **Total active** | **≈ 20 000 (≈ 55 % of tile)** |

If the design doesn't fit, cut in this order: (1) comparator preamp, (2) VREF buffer
(drive the DAC from the bandgap directly, at a lower sample rate), (3) resolution down to 7 bits.

## Pin plan

### Analog

| Pin | Name | Dir | Description |
|---|---|---|---|
| `ua[0]` | VIN | in | ADC input, 0 … VREF |
| `ua[1]` | AMUX / VREF_EXT | in/out | `REF_SEL` = 1: external reference **input** (1.0–1.8 V, decouple off-chip). `REF_SEL` = 0: analog debug **output** selected by `AMUX_SEL`. Measure it with a high-impedance meter only. |

When `REF_SEL` = 1, the on-chip logic forces the AMUX output switch off, so the debug output never fights the external source.

### Digital

| Pin | Internal mode (`MODE`=0) | External mode (`MODE`=1) |
|---|---|---|
| `clk` | SAR clock | unused |
| `rst_n` | active-low reset | active-low reset |
| `ui[0]` | START (rising edge starts a conversion) | EXT_D0 |
| `ui[2:1]` | AMUX_SEL: 00 Hi-Z, 01 VBG, 10 VREF buffered, 11 VPTAT | EXT_D[2:1] |
| `ui[3]` | BG_PD: 1 = power down the bandgap and buffer | EXT_D3 |
| `ui[7:4]` | unused (tie low) | EXT_D[7:4] |
| `uo[7:0]` | D[7:0], conversion result | D[7:0] mirrors EXT_D (loopback check) |
| `uio[0]` | MODE (in) | MODE (in) |
| `uio[1]` | unused | EXT_SAMPLE: 1 = track, 0 = hold (in) |
| `uio[2]` | unused | EXT_CMP_CLK (in) |
| `uio[3]` | REF_SEL: 0 internal, 1 `ua[1]` (in) | REF_SEL (in) |
| `uio[4]` | CMP_OUT (out) | CMP_OUT (out) |
| `uio[5]` | EOC (out) | low |
| `uio[7:6]` | INSEL: 00 VIN, 01 VPTAT (temp sensor), 10 VBG (needs `REF_SEL`=1), 11 VGND (offset) (in) | INSEL (in) |

`uio_oe` = `8'b0011_0000`.

## Operating scenarios

| Scenario | Settings | What it shows |
|---|---|---|
| Normal ADC | MODE=0, REF_SEL=0, INSEL=00 | VIN digitized against the internal bandgap |
| Temperature sensor | MODE=0, REF_SEL=0, INSEL=01 | Code proportional to absolute temperature |
| Bandgap check (DMM) | MODE=0, REF_SEL=0, AMUX_SEL=01 | VBG on `ua[1]` |
| Bandgap check (ADC) | MODE=0, REF_SEL=1 (known VREF on `ua[1]`), INSEL=10 | VBG digitized against a known reference |
| Bandgap fallback | MODE=0, REF_SEL=1, INSEL=00 | ADC works even if the bandgap is dead |
| Analog core debug | MODE=1 | RP2040 runs the SAR algorithm itself |

## Open questions

1. SAR logic implementation: synthesized sky130 standard cells placed by script, or hand-placed standard-cell DFFs and gates?
2. MIM placement vs. our own met4 power straps: since we draw the straps, keep them clear of the
   DAC array (or use `cap_mim_m4_2` and route power around it). Prior TT SARs (TT06, 26d) used MIM successfully.
3. Pad series resistance and capacitance of `ua[]`: the numbers are on tinytapeout.com/specs/analog,
   which wasn't reachable from the build environment. Fill them in here.
