# Floorplan v3 (2026-11-14) — tt_um_chiranjitpatel_sar_adc

**Status: used for M1 (2026-11-14).** Power stripes start at y = 1 (bottom power-tie straps). Source: `layout/floorplan_v3.py` → `layout/floorplan_v3.json`, picture
`material/layout/floorplan_v3.png`. The earlier floorplan (`floorplan.md`, `floorplan.py`, `floorplan.json`,
`floorplan.png`) is kept unchanged; the M0 frame still uses it until M1 integration moves to v3.
Coordinates in µm from the tile's bottom-left corner; tile 161.00 × 225.76 µm.

## Why a v3

The scripted M1 cells (2026-11-12) are larger than the v1/v2 estimates. bandgap_core alone is 71.7 × 104 µm,
but the v2 left column was 54 µm wide. v3:
- **Left column: 72 µm** (x = 7 … 78.7).
- **Middle VDPWR/VGND stripe pair moved** from x = 64–69 to **x = 83–88**.
- **Right (M2) half: 63.5 µm** (x = 90 … 153.5). The M2 blocks are not drawn yet; their outlines are estimates.

## Blocks

| Block | x0 – x1 | y0 – y1 | Size | Milestone | Status | Note |
|---|---|---|---|---|---|---|
| bias_gen | 7.0 – 60.6 | 190.5 – 214.4 | 53.6 × 23.9 | M1 | drawn | top left |
| bandgap_core | 7.0 – 78.7 | 84.0 – 188.0 | 71.7 × 104.0 | M1 | drawn | OTA + MIM, sources, startup, PNP array, R1/R2 |
| vref_filt | 7.0 – 59.8 | 42.0 – 81.5 | 52.8 × 39.5 | M1 | drawn | **rotated 180°**: vbg pin at the top right, next to the bandgap's vbg; vbg_f at the bottom left |
| ptat_out | 7.0 – 38.2 | 7.0 – 38.4 | 31.2 × 31.4 | M1 | drawn | vptat runs along the bottom corridor to the input mux |
| vref_sel | 41.0 – 71.1 | 7.0 – 37.1 | 30.1 × 30.1 | M1 | drawn | pad (TG) runs along the bottom corridor to `ua[1]` (x = 132.9) |
| vref_buf | 90.0 – 133.1 | 7.0 – 64.3 | 43.1 × 57.3 | M1 | drawn | vref to vref_sel (bottom corridor) and up to dac_sw |
| inmux | 135.0 – 153.5 | 7.0 – 53.0 | 18.5 × 46.0 | M2 | estimate | VIN from `ua[0]` (x = 152.3) |
| dac_sw | 90.0 – 153.5 | 67.0 – 77.0 | 63.5 × 10.0 | M2 | estimate | under the array |
| cap_dac | 93.0 – 151.0 | 80.0 – 138.0 | 58.0 × 58.0 | M2 | estimate | **3 µm unit pitch** (v2: 4 µm, 72 × 72) |
| comparator | 93.0 – 121.0 | 141.0 – 161.0 | 28.0 × 20.0 | M2 | estimate | right above the array: short, shielded vtop |
| vcm_gen | 123.0 – 153.5 | 141.0 – 163.0 | 30.5 × 22.0 | M2 | estimate | next to the comparator |
| adc_digital | 90.0 – 153.5 | 168.0 – 214.0 | 63.5 × 46.0 | M2 | estimate | LibreLane macro (v2: 82 × 30) |

Blocks use 24 180 µm² (67 % of the tile). The drawn M1 cells use 15 178 µm².
Checks (in the script): all blocks inside the tile, no overlaps, ≥ 1 µm from every power stripe, and
no block on a routing corridor.

## Routing corridors (reserved for the top-level wiring)

Block internals already use met2/met3 (and met4 for the MIM caps in bandgap_core), so the wiring between blocks
runs in these gaps:

| Corridor | Area | Carries |
|---|---|---|
| G1 | between bias_gen and bandgap_core (y 188.0–190.5) | pbias, pd to the bandgap's left buses |
| G2 | between bandgap_core and vref_filt (y 81.5–84.0) | vbg (bandgap → vref_filt's top-right pin), vgp → ptat_out |
| G3 | between vref_filt and the bottom row (y 38.4–42.0) | vbg_f (vref_filt bottom left → R1 → vref_buf), vgp |
| R1 | right edge of the left column (x 79.5–82.0) | vertical runs: nbias, vbg_f, en_buf, control pins from T1 |
| R2 | beside vref_filt (x 60.5–78.7, y 42–81.5) | spare / vertical runs on the vref_filt side |
| B1 | along the bottom (y 1.6–6.4, met3 under the stripes) | pad → `ua[1]`, VIN from `ua[0]`, vptat → inmux, vref → vref_sel |
| T1 | along the top (y 214.6–216.6, met2) | REF_SEL `uio_in[3]`, BG_PD `ui_in[3]`, VREF_OE `ui_in[1]` → R1 (M1, no digital block); the output tie bar stays at y = 219.5 (met3) |

Routes cross the middle stripes on met3 or met2 (under the met4 stripes). No met5 anywhere.

## Changes to the rest of the design

- **M0/M1 frame:** the middle stripe pair moves to x = 83–88. `m0_frame.py` reads the floorplan JSON, so M1
  integration switches it to `floorplan_v3.json`.
- **cap_dac** at a 3 µm unit pitch (was 4 µm). This was open point 2 of floorplan v1; check the bottom-plate
  routing when it's drawn.
- **adc_digital** gets a 63.5 × 46 µm outline for LibreLane (was 82 × 30).
- vgp (a DC gate net) runs from the bandgap's right bus through G2/G3 to ptat_out at the bottom left.

## Open points for review

1. vref_sel sits at the bottom left, so the `ua[1]` pad path runs about 70 µm along the bottom corridor on met3.
   Estimated a few Ω and ~10 fF, small next to the pad budget (500 Ω, 5 pF), but it will be checked after extraction.
2. The M2 outlines (cap_dac, adc_digital, comparator, vcm_gen, inmux, dac_sw) are estimates. The right half has
   about 2 µm of vertical slack between blocks.
3. The R1 corridor is only 2.5 µm wide (about 3 tracks), because bandgap_core fills the column. Overflow goes into
   R2 (beside vref_filt, 18 µm wide) and the free space right of bias_gen (x 60.6–78.7), which only the
   bandgap's 104 µm stretch has to bypass.
