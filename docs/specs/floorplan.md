# Floorplan (chunk 0b) — tt_um_chiranjitpatel_sar_adc

**Status: approved 2026-11-08; revised the same night after the bandgap Phase 2 resize (see below).** Source of truth: `layout/floorplan.py` → `layout/floorplan.json`
(read by the layout scripts and the M0 frame). Picture: `material/layout/floorplan.png`.
Coordinates in µm from the tile's bottom-left corner; tile 161.00 × 225.76 µm (`tt_analog_1x2.def`).

## Block placement

| Block | x0 – x1 | y0 – y1 | Area µm² | × device area | Milestone | Why here |
|---|---|---|---|---|---|---|
| bias_gen | 8 – 30 | 188 – 214 | 572 | 3.0 | M1 | top-left, short pbias/nbias runs into the bandgap below |
| bandgap_core | 8 – 62 | 92 – 186 | 5076 | 1.2 (1.6 without the MIM) | M1 | largest analog block (OTA with a 2.1 pF MIM over its devices, PNP array, R1/R2, startup) |
| vref_filt | 8 – 62 | 46 – 88 | 2268 | 1.5 | M1 | directly under the bandgap that feeds it (cell 52.8 × 39.5) |
| ptat_out | 8 – 42 | 6 – 42 | 1224 | 2.7 | M1 | bottom left (cell 31.2 × 31.4); `vptat` runs along the bottom to the input mux |
| vref_buf | 72 – 116 | 38 – 74 | 1584 | 1.6 | M1 | between the filter and the DAC switches: short `vref` |
| vref_sel | 118 – 150 | 6 – 20 | 448 | 6.1 | M1 | on top of the `ua[1]` pin (x = 132.94) |
| inmux | 118 – 150 | 24 – 50 | 832 | 5.4 | M2 | VIN from `ua[0]` (x = 152.26) up the right edge |
| dac_sw | 76 – 148 | 78 – 88 | 720 | 2.1 | M2 | 9 switch cells under the array's bottom-plate groups |
| cap_dac | 76 – 148 | 90 – 162 | 5184 | 2.2 | M2 | 16 × 16 MIM units + dummy ring (18 × 18 at 4 µm) |
| comparator | 86 – 114 | 164 – 184 | 560 | 4.0 | M2 | right above the array: short, shielded `vtop` (rule 5) |
| vcm_gen | 116 – 150 | 164 – 184 | 680 | 1.5 | M2 | next to the comparator's `inn` |
| adc_digital | 71 – 153 | 186 – 216 | 2460 | 1.0 × (1289 µm² cells / 0.55) | M2 | under the top pins; LibreLane macro |
| reserve_top | 34 – 62 | 188 – 214 | 728 | — | — | spare (was ptat_out) |
| reserve_left | 44 – 62 | 6 – 42 | 648 | — | — | spare |
| reserve_right | 72 – 116 | 6 – 34 | 1232 | — | — | e.g. a larger VREF reservoir cap |

Used 21 608 µm² (59 % of the tile), reserve 2 608 µm².

## Power

Six vertical met4 stripes, 2 µm wide, y = 5 … 217 µm: (VDPWR, VGND) pairs at x = 1/4 (left edge),
64/67 (between the left column and the DAC/digital area) and 154.5/157.5 (right edge, right of the
`ua[0]` route). TT requires the stripes to start in the bottom 10 µm and reach the top 10 µm (≥ 215.76);
they end at 217 so they stay clear of the output-pin tie stubs (the middle pair sits under the
`uio_out` pins at x = 63.9–69.5). No stripe crosses the MIM array or the digital block, because both use
met4 themselves (MIM top plates; the macro's own power grid).

## Routing layers

- Inside blocks: li1, met1, met2 (met3 where needed).
- Between blocks: met3 (passes under the met4 stripes).
- met4: power stripes, MIM top plates, pins only. **No met5** (TT power grid).
- Long sensitive routes: `vptat` and `vbg` (high impedance, slow) from the left column to the input mux
  (bottom right): met3, kept away from the digital block and the DAC switches. `vtop` stays inside the
  DAC/comparator area and gets a grounded shield (rule 5).

## Milestone views

- **M0 (now):** frame + all six stripes + the 24 outputs tied to VGND through a met3 bar at y = 219.5.
- **M1:** adds the blue blocks. REF_SEL / VREF_OE / BG_PD come straight from `uio_in[3]`, `ui_in[1]`,
  `ui_in[3]`; outputs stay tied.
- **M2:** adds the orange blocks. The digital macro drives the outputs, and the tie bar goes away.

## Open points for review

1. The digital macro size (82 × 30 µm, ≈ 52 % utilization) is an estimate until the first LibreLane run.
2. The DAC array outline assumes a 4 µm unit pitch, to leave room for bottom-plate routing. A tighter
   pitch (≈ 3 µm) would free ≈ 2000 µm², if the common-centroid routing allows it.
3. pbias/nbias run from the top-left to the right column (vcm_gen, comparator preamp, vref_buf): ≈ 150 µm on
   met3. These are high-impedance gate-bias nets; each consumer gets a local decoupling cap.

## Revision 2026-11-08 (night)

The bandgap Phase 2 Monte Carlo made the matched devices larger (`sim/bandgap/README.md`): the OTA input pair,
loads and Miller cap, the PMOS current sources, and R1/R2/R3 (0.69/4 units). Changes:
- bandgap_core grows from 54 × 82 to 54 × 94 µm.
- vref_filt grows from 54 × 34 to 54 × 42 µm (14 resistor units, 7 caps for B7).
- ptat_out (now 31 × 31 µm) moves to the bottom left, and its old place becomes reserve_top.
`vgp` (a DC gate net) now runs about 60 µm from the bandgap down to ptat_out on met3.
