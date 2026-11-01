# Top-level specification — `tt_um_adc`

**Status: DRAFT v0.1** — the pin plan and tile size need sign-off before layout starts.

## Block diagram

```
                 VDPWR (1.8 V)
                    │
   ┌────────────────┴─────────────────────────────────────────┐
   │                                                          │
   │  ┌──────────┐  vbg   ┌────────┐ vref_int                 │
   │  │ Bandgap  ├───────►│ VREF   ├────┐                     │
   │  │ + start  │        │ buffer │    │   ┌───────┐         │
   │  └────┬─────┘        └────────┘    ├──►│ ref   │ vref    │
   │       │ en_bg                      │   │ select├──┐      │
   │                       ua[2] ───────┘──►│       │  │      │
   │                     (ext VREF)         └───────┘  │      │
   │                                                   ▼      │
   │  ua[0] vin ──►┌────────────┐  ┌──────────┐   ┌─────────┐ │
   │               │ 8-bit cap  ├─►│ dynamic  ├──►│ SAR     ├─┼─► uo[7:0]  D[7:0]
   │               │ DAC + S/H  │  │comparator│   │ logic   ├─┼─► uio[5]   EOC
   │               └─────▲──────┘  └──────────┘   └────┬────┘ │
   │                     └──────── DAC code ◄──────────┘      │
   │                                (or external, from ui[7:0])│
   │  analog debug mux ───────────────────────────────────────┼─► ua[1]
   └──────────────────────────────────────────────────────────┘
```

## Global specs

| Parameter | Value |
|---|---|
| Process | sky130 |
| Supply | VDPWR = 1.8 V only (no VAPWR) |
| Tiles | **2x2** (≈ 334 × 225 µm) — 1x2 is too small for the DAC and bandgap together |
| Analog pins | **3** (`ua[0]`–`ua[2]`) |
| Total supply current | < 500 µA while converting, < 10 µA powered down (target) |
| Clock | `clk` = SAR clock, 1 MHz nominal (≈ 100 kS/s), up to 10 MHz (stretch) |

## Pin plan (draft)

### Analog

| Pin | Name | Dir | Description |
|---|---|---|---|
| `ua[0]` | VIN | in | ADC input, 0 … VREF |
| `ua[1]` | AMUX | out | Analog debug mux output (VBG, buffered VREF, PTAT voltage, …) — measure with a high-impedance meter only |
| `ua[2]` | VREF_EXT | in | External reference, used when `ref_sel` = 1. Fallback if the bandgap fails |

### Digital

| Pin | Name | Dir | Description |
|---|---|---|---|
| `clk` | CLK | in | SAR clock |
| `rst_n` | RST_N | in | Active-low reset of the SAR logic |
| `ui[0]` | START / EXT_D0 | in | Internal mode: rising edge starts a conversion. External mode: DAC bit 0 |
| `ui[7:1]` | EXT_D[7:1] | in | External mode: DAC bits 7..1 |
| `uo[7:0]` | D[7:0] | out | Conversion result (internal mode) |
| `uio[0]` | MODE | in | 0 = internal SAR, 1 = external SAR (RP2040 drives the DAC and reads the comparator) |
| `uio[1]` | EXT_SAMPLE | in | External mode: 1 = track VIN, 0 = hold |
| `uio[2]` | EXT_CMP_CLK | in | External mode: comparator clock |
| `uio[3]` | REF_SEL | in | 0 = internal bandgap reference, 1 = `ua[2]` |
| `uio[4]` | CMP_OUT | out | Comparator output (both modes) |
| `uio[5]` | EOC | out | End of conversion (internal mode) |
| `uio[7:6]` | AMUX_SEL[1:0] | in | Debug mux select: 00 off (Hi-Z), 01 VBG, 10 VREF buffered, 11 VPTAT |

`uio_oe` = `8'b0011_0000`.

**Why external mode:** the RP2040 can run the SAR algorithm itself, which lets us measure
the DAC and comparator even if the on-chip SAR logic is broken.

## Open questions

1. Is the cost of 3 analog pins OK, or should we drop `ua[2]` (and lose the external-reference fallback)?
2. SAR logic implementation: synthesized sky130 standard cells placed by script, or hand-built from standard-cell DFFs and gates?
3. Unit capacitor: MIM (`cap_mim_m3_1`, uses met3/met4 — check that it doesn't conflict with TT power on met4) vs. custom MOM fingers in met1–met3.
