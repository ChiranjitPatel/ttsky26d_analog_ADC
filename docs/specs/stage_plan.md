# Stage plan — bottom-up design and integration

**Status: DRAFT v0.1**

The design is built bottom-up. Each stage is **one block with a clear interface and its own
testbench**. Integration adds **one proven block at a time**, so a failure always points to the
newest block or its interface.

## Rules for every stage

1. **Don't start a stage until the stages it depends on are done** (see "Depends on").
2. Each stage goes through the same steps. A stage is **done** only when all steps up to the
   current project phase are checked:

   | Step | Tool | Output |
   |---|---|---|
   | a. Schematic + symbol | xschem | `xschem/<cell>.sch`, `xschem/<cell>.sym` |
   | b. Pre-layout sim, Phase 1 (tt, 27 °C, 1.80 V) | ngspice | `sim/<block>/tb_*.spice`, results in the spec Status table |
   | c. Pre-layout sim, Phase 2 (corners, temp, supply, Monte Carlo) | ngspice | same testbenches, swept |
   | d. Layout | KLayout | `layout/<cell>.gds` |
   | e. DRC | KLayout deck + Magic | clean |
   | f. Extraction + LVS | Magic + netgen | LVS match |
   | g. Post-layout sim (Phase 3) | ngspice | key testbenches on the extracted netlist |

3. Steps a–b come first for all stages, because they're cheap and catch architecture problems early.
   Layout (d–g) starts per block once its Phase 2 results are good.
4. Testbenches that touch a pad include the pad model: 500 Ω in series and 5 pF to ground (CLAUDE.md rule 2).
5. Every block with a power-down input is also tested powered down (leakage, and correct restart).
6. Record the result of each stage in the Status table at the bottom, with the date.

## Block stages

Targets marked † are stage-level design targets. They don't appear in the block specs, because
the specs only define what the final system must do.

### Stage 0 — Device sanity
- **Goal:** confirm the PDK, models and tools behave as expected before any design work.
- **Cells:** none (primitive devices only).
- **Testbenches:** `sim/devices/`. nfet/pfet Id–Vgs and Id–Vds (W/L used later), gm/Id curves;
  PNP `pnp_05v5_W3p40L3p40` Vbe vs. current and temperature; `res_xhigh_po_0p35` sheet resistance;
  `cap_mim_m3_1` 2 × 2 µm capacitance.
- **Exit:** the numbers match the PDK documentation within a few %; gm/Id lookup tables saved for sizing.
- **Depends on:** PDK install.

### Stage 1 — Bias current reference
- **Goal:** a supply-independent bias current for the OTA, the VREF buffer and the comparator tail (if needed).
- **Cells:** `bias_gen` (β-multiplier or a PTAT-mirror tap from the bandgap; decide in stage).
- **Targets†:** I_bias = 1 µA nominal, mirrored outputs; changes < 10 % for VDPWR 1.62–1.98 V (Phase 2);
  has a startup circuit and powers down with `bg_pd`.
- **Testbenches:** `tb_bias_op`, `tb_bias_startup` (supply ramp from 0 V, CLAUDE.md rule 7).
- **Depends on:** 0.

### Stage 2 — Error amplifier (OTA)
- **Goal:** the bandgap's error amplifier. The same topology may be reused for the VREF buffer (stage 5).
- **Cells:** `ota` (5-transistor first; two-stage only if the gain is too low).
- **Targets†:** DC gain ≥ 50 dB; phase margin ≥ 60 ° with the bandgap load; input offset σ ≤ 2 mV
  (Phase 2 Monte Carlo); input common-mode range covers Vbe ≈ 0.55–0.75 V.
- **Testbenches:** `tb_ota_ac` (gain, unity-gain bandwidth, phase margin), `tb_ota_dc` (input range), `tb_ota_mc` (offset).
- **Depends on:** 1.

### Stage 3 — Bandgap core + startup
- **Goal:** VBG ≈ 1.20 V.
- **Cells:** `bandgap_core` (PNP 1:8 array, resistors, OTA from stage 2, startup).
- **Specs:** B1, B2, B3 in Phase 1; B4–B8 in Phase 2; B9 at layout.
- **Testbenches:** `tb_bg_op`, `tb_bg_startup`, `tb_bg_line`, `tb_bg_temp`, `tb_bg_psrr`.
- **Exit check:** the circuit must start from 0 V and must not stay in the zero-current state at any corner.
- **Depends on:** 2.

### Stage 4 — PTAT branch
- **Goal:** VPTAT for the temperature sensor, without loading the core.
- **Cells:** `ptat_out` (mirrored PTAT current into its own resistor).
- **Specs:** B10 in Phase 1; B11 in Phase 2; B12–B13 are calculated from B11 and the ADC LSB.
- **Testbenches:** `tb_bg_ptat`, plus a check that loading VPTAT changes VBG by < 0.1 mV.
- **Depends on:** 3.

### Stage 5 — VREF buffer
- **Goal:** drive the DAC reference and (optionally) the `ua[1]` pad from VBG.
- **Cells:** `vref_buf` (unity-gain, based on the stage 2 OTA or a variant of it), `vref_sel`
  (internal/external selection + output switch, controlled by `REF_SEL` and `VREF_OE`).
- **Targets†:** VREF settles to within 0.5 LSB (2.3 mV) by the end of each bit cycle while driving the DAC
  (2.5 pF switched); stable driving pad + probe (5 pF, 500 Ω, plus 10 pF probe); phase margin ≥ 45 °.
- **Testbenches:** `tb_vref_step` (DAC-like load steps), `tb_vref_pad` (stability with pad), `tb_vref_sel`.
- **Depends on:** 2 (topology), 3 (input).

### Stage 6 — Comparator
- **Goal:** decide `vtop` vs. the comparison voltage within one bit cycle, with low kickback.
- **Cells:** `comp_strongarm`, `sr_latch`, wrapper `comparator`.
- **Specs:** A10 in Phase 1; A7, A8 in Phase 2.
- **Targets†:** kickback on a 2.5 pF top-plate node ≤ 0.25 LSB (1.2 mV) after the decision (CLAUDE.md rule 5).
- **Testbenches:** `tb_cmp`, `tb_cmp_kickback`, `tb_cmp_mc`.
- **Depends on:** 0.

### Stage 7 — Sampling switch + input mux
- **Goal:** select the ADC input and sample it onto the DAC.
- **Cells:** `tgate`, `inmux` (VIN / VPTAT / VBG / VGND), `sample_sw`.
- **Specs:** A9, A14.
- **Testbenches:** `tb_sample` (VIN step through the pad model onto 2.5 pF), `tb_inmux`.
- **Depends on:** 0.

### Stage 8 — Cap DAC
- **Goal:** binary-weighted 256-unit MIM DAC.
- **Cells:** `cap_unit` (one MIM unit cell + dummy variant), `cap_dac` (16 × 16 common-centroid array
  with bottom-plate switches).
- **Specs:** A13 in Phase 2; the linearity part of A4/A5 for the DAC alone.
- **Steps:** unit cell → 2-bit sub-array check → full array. The array layout is script-generated (KLayout Python).
- **Testbenches:** `tb_dac` (step through all 256 codes, ideal comparator), `tb_dac_mc`.
- **Depends on:** 0.

### Stage 9 — SAR logic
- **Goal:** sequencer + successive-approximation register + external-mode multiplexing.
- **Cells:** `sar_logic` (sky130_fd_sc_hd standard cells).
- **Steps:** behavioural Verilog first (iverilog/cocotb in `test/`) → gate-level netlist →
  transistor-level ngspice simulation with ideal analog parts.
- **Targets†:** correct code for all 256 inputs with an ideal comparator; works at 10 MHz (A12 stretch);
  `MODE`=1 passes `ui[7:0]` straight to the DAC; all unused outputs tied to VGND.
- **Depends on:** none (digital); for ngspice, 0.

## Integration stages

Each step uses proven blocks plus **ideal models for everything that isn't integrated yet**.

| Stage | Adds | Ideal (still modelled) | Proves | Specs |
|---|---|---|---|---|
| **I1** Analog core | DAC (8) + comparator (6) + sampling switch (7) | SAR logic (behavioural, in-netlist), VREF (ideal source), input (ideal) | The analog path converts correctly; kickback in the real loop | A4, A5 (ideal ref) |
| **I2** Full ADC | + SAR logic (9) | VREF, input mux | Timing between logic and comparator; `EOC`; external mode | A3, A4, A5, A6, A11 |
| **I3** Self-referenced ADC | + bandgap (3), VREF buffer (5), bias (1) | input | VREF settling under real DAC switching; supply coupling | A4–A6 with the real reference |
| **I4** Top level | + PTAT branch (4), input mux (7), pads, power straps, `tt_um_chiranjitpatel_sar_adc` pins | — | All scenarios in `top_level.md`; temperature-sensor mode; external-reference fallback | all |

After I4: top-level layout, full-chip DRC/LVS, post-layout simulation of I2–I4, then the TT precheck in GitHub Actions.

## Suggested order

Stages 6–9 don't depend on the bandgap chain (1–5), so the two chains can run side by side:

```
0 ─┬─ 1 ─ 2 ─ 3 ─ 4 ─ 5 ──────────────┐
   └─ 6 ─ 7 ─ 8 ─ 9 ── I1 ─ I2 ───────┴─ I3 ─ I4
```

The plan is to start with the **bandgap chain** (stage 0 → 1 → 2 → 3) to get a first end-to-end
pass through simulation, layout and LVS on a small block.

## Status

| Stage | a | b | c | d | e | f | g | Notes |
|---|---|---|---|---|---|---|---|---|
| 0 Devices | — | | | — | — | — | — | |
| 1 Bias | | | | | | | | |
| 2 OTA | | | | | | | | |
| 3 Bandgap | | | | | | | | |
| 4 PTAT | | | | | | | | |
| 5 VREF buffer | | | | | | | | |
| 6 Comparator | | | | | | | | |
| 7 Switch + mux | | | | | | | | |
| 8 Cap DAC | | | | | | | | |
| 9 SAR logic | | | | | | | | |
| I1 Analog core | | | | | | | | |
| I2 Full ADC | | | | | | | | |
| I3 Self-referenced | | | | | | | | |
| I4 Top level | | | | | | | | |

a = schematic, b = Phase 1 sim, c = Phase 2 sim, d = layout, e = DRC, f = LVS, g = post-layout sim.
