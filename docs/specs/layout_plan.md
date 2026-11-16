# Layout plan — milestones and chunks

**Status: DRAFT (2026-11-08).** 2026-11-12: Claude scripts all M1 chunks; the designer reviews. Deadline: **TTSKY26d, 2026-12-01.**
Layout freeze: **2026-11-26** (agreed 2026-11-08; 5 days for final DRC/LVS/precheck/submission). It
replaces CLAUDE.md rule 8's earlier "3 weeks before the deadline", which would have been 2026-11-10.

Template: `tt_analog_1x2.def` from TinyTapeout/tt-support-tools (`tech/sky130A/def/analog/`; the
`_3v3` variant is only for VAPWR designs). 161.00 × 225.76 µm; `ua[0]`/`ua[1]` on the bottom edge at
x = 152.26 / 132.94 µm; digital pins on the top edge; all pins on met4.

## Milestones (each one is a complete, submittable chip)

Every milestone is a full tile: pins, power stripes, top cell, DRC/LVS/precheck clean. At any time, the
last milestone that passed precheck is what gets submitted.

| Milestone | Contents | Measurable on silicon |
|---|---|---|
| **M0 Frame** | outline + pins from the DEF, power stripes, unused outputs tied low | — (proves the flow and the CI precheck) |
| **M1 Reference chip** | bias_gen, bandgap_core + ptat_out, vref_filt, vref_buf, vref_sel → `ua[1]` | VREF on `ua[1]` with a DMM; bandgap TC on a hot plate |
| **M2 Full ADC** | + cap_dac, comparator, vcm_gen, inmux, adc_digital | everything in `docs/info.md` |

M1 has no digital block: `REF_SEL`, `VREF_OE`, `BG_PD` are wired straight from their pins
(`uio[3]`, `ui[1]`, `ui[3]`); all outputs tied low.

## Chunks

Each chunk is one cell, DRC + LVS clean on its own before it's placed. Before a cell is drawn, its
block-level corner sweep (Phase 2) is run, so sizes are final when layout starts. Each hand-drawn cell
gets a brief (devices, sizes, matching groups, pin positions, target outline).

| # | Chunk | Who | Target |
|---|---|---|---|
| **M0** | Frame: DEF outline/pins, power stripes, output ties, CI precheck green | Claude | **Done Nov 8**: TT precheck green in CI (gds run 46, commit 5849aa6) |
| 0b | Floorplan: final position and outline of every block | Claude (designer reviews) | Nov 10 — draft Nov 8 (`docs/specs/floorplan.md`) |
| 1a | bias_gen | Claude (scripted; designer reviews) | **Done Nov 12**: 53.6 × 23.9 µm, DRC 0 (Magic + KLayout), LVS match (`gen_bias_gen.py`) |
| 1b | ota | Claude (scripted; designer reviews) | **Done Nov 12**: 68.7 × 47.8 µm, DRC 0, LVS match (`gen_ota.py`; also inside bandgap_core) |
| 1c | PNP 3×3 common-centroid array + R1/R2 unit-resistor chains (scripted) | Claude | Nov 11 — cells done Nov 8 (`pnp_array`, `bg_res` regenerated with 0.69/4 units; DRC/LVS clean, `layout_briefs/scripted_cells.md`); bandgap Phase 2 done (corners 63/63; MC σ 17.6 mV, B6 decision open) |
| 1d | bandgap_core assembly (1b + 1c + current sources + startup) | Claude (scripted; designer reviews) | **Done Nov 12**: 71.7 × 104 µm, DRC 0, LVS match (`gen_bandgap_core.py`) |
| 1e | ptat_out (one PMOS + resistor chain) | Claude | Nov 14 — done Nov 8: Phase 2 (`sim/ptat/sensor.md`, B13 decision open) + layout (16/8 + 0.69/4, DRC/LVS clean) |
| 1f | vref_filt (resistor chain + MOS cap, scripted) | Claude | Nov 14 — done Nov 8: 1.6 MΩ + 5.5 pF for B7, layout DRC/LVS clean; VREF-chain corners in `sim/vref/corners.md` |
| 1g | vref_buf + reservoir cap | Claude (scripted; designer reviews) | **Done Nov 12**: 43.1 × 57.3 µm, DRC 0, LVS match (`gen_vref_buf.py`) |
| 1h | vref_sel logic + `ua[1]` transmission gate | Claude (scripted; designer reviews) | **Done Nov 12**: 30.1 × 30.1 µm, DRC 0, LVS match (`gen_vref_sel.py`) |
| **M1** | Integration, LVS, post-layout sim, precheck | Claude | **Done Nov 14** (`layout/m1_top.py`, floorplan v3): Magic DRC 0, KLayout 0, LVS match, CI precheck passed (474f254); post-layout sim (R+C) matches the schematic within 1 mV / 1 dB, B7 met in all 45 corners after two fixes (`sim/m1/`) |
| 2a | DAC unit cell + 16 × 16 common-centroid MIM array (scripted) | Claude | **Done Nov 16**: `cap_array` 62.3 × 63.4 µm, DRC 0 (Magic + KLayout), LVS match (`gen_cap_dac.py`) |
| 2b | dac_sw (one cell, used 9×) | Claude (taken over) | **Done Nov 16**: `dac_sw_row` (all 9) 47.1 × 5.7 µm, full custom, clean (`gen_dac_sw.py`) |
| 2c | comparator (with preamp) | Claude (taken over) | **Done Nov 16**: 36.4 × 38.5 µm, clean (`gen_comparator.py`) |
| 2d | vcm_gen + top-plate switch | Claude (taken over) | **Done Nov 16**: 17.5 × 49.5 µm, clean (`gen_vcm_gen.py`); the top-plate switch is in the comparator cell |
| 2e | inmux | Claude (taken over) | **Done Nov 16**: 15.2 × 5.6 µm, full custom, clean (`gen_inmux.py`) |
| 2f | adc_digital place & route (LibreLane / OpenROAD, sky130_fd_sc_hd) | Claude | **Done Nov 16**: 63.5 × 47.3 µm, 221 cells; route/Magic/KLayout DRC 0, LVS 0, antenna 0, setup +27.4 ns / hold +0.12 ns at 100 ns (`layout/digital/`) |
| **M2** | Integration, LVS, post-layout sim, precheck | both | **Nov 24–26** |
| — | Freeze; final checks; submission | both | Nov 26 – Dec 1 |

In parallel (Claude): Phase 2 block sweeps (before each cell), I4 full-chip simulation, post-layout
simulation of each cell as it is finished.

## Tools

- Layout: KLayout (designer's 0.30.8; precheck uses 0.30.4). Extraction/LVS: Magic + netgen.
- Digital P&R: LibreLane in Docker (`ghcr.io/librelane/librelane:3.0.17`). Nix's LibreLane binary
  cache (librelane.cachix.org) is blocked by this environment's network policy; Docker works.

## Status 2026-11-12: all M1 cells scripted

Every M1 cell is DRC clean (Magic and the TT KLayout deck) and LVS-matched to its schematic. Pictures are in
`material/layout/`. The scripted cells are bigger than the 2026-11-08 floorplan estimates, so the left column
must be ~72 µm wide (bandgap_core is 71.7 µm). That moves the middle VDPWR/VGND stripe pair from x = 64–69 to
~82–87 and narrows the right (M2) half to ~64 µm. M1 integration comes next: floorplan v3, M0 frame with the
moved stripes, block placement, inter-block routing in reserved corridors, full-chip LVS and precheck.

## M1 integration (2026-11-14)

`layout/m1_top.py` builds the submission GDS/LEF (`gds/`, `lef/`) from the M0 frame recipe and floorplan v3.
- **Blocks:** the six M1 cells at their v3 positions (vref_filt rotated 180°).
- **Wiring:** routed in the reserved corridors, crossing the stripes on met3. The control pins (`ui_in[3]` BG_PD,
  `ui_in[1]` VREF_OE, `uio_in[3]` REF_SEL) come straight in (no digital block in M1). The pad route runs to `ua[1]`.
- **Power:** each block's rails are strapped to its nearest stripes. **Internal ties:** met3 straps along the bottom
  (VDPWR y = 1.3, VGND y = 6.7) with via3 into all three stripes of each net; the stripes now start at y = 1.
  The LVS confirms each supply is one net and the two are not shorted.
- **Results:** Magic DRC 0. KLayout feol/beol/offgrid 0. LVS against `layout/cells/m1_top_ref.spice`: circuits match
  uniquely; the only port messages are for the 23 unused TT pins. The precheck functions run locally (top/cell
  names, analog pins, boundary, pin positions, power pins, layers) all pass.
- **Build lessons:** read the block GDS files before the DEF, and start from an empty cell before `def read`
  (otherwise Magic edits the wrong cell). Delete stale `.mag` files in the build folder.

## M1 post-layout (2026-11-14)

`layout/m1_pex.py` extracts the submission GDS flat with R and C (Magic 8.3.623 in the LibreLane image; the local
8.3.411 drops the resistors). `sim/m1/` runs the same pin-level tests on the schematic and on the extraction.
Details in `sim/m1/README.md`, numbers in `sim/m1/results.md` and `sim/m1/corners_b7.md`.
- **Found:** current mirrors drawn with wider fingers than their 2/2 reference mirror the wrong current
  (narrow-width effect; LVS merges parallel devices and can't see it). OTA M5/M7 were 11–20 % low, which cost
  1.4 dB of B7 at 1 MHz; the vref_buf tail was 26 % high.
  Fixed: bandgap_core draws M5 as 2 × 2/2 and M7 as 4 × 2/2 (same 71.7 × 104 µm cell); vref_buf's tail is
  2 × 8/2 in both schematic and layout (9.6 µA as before).
- **Found:** B7 at 1 MHz missed by up to 1 dB in hot / fs corners (schematic too). Fixed with a 2.5 pF MIM
  (`vbg_f` to VGND) stacked over vref_filt, which used only met1/met2: no area cost.
- **Result:** VBG 1.2098 V (schematic 1.2105 V); B7 tt 23.8 dB at 1 MHz, corners ≥ 22.7 dB at 1 MHz and
  ≥ 31.3 dB DC at 1.62 V; startup 24 µs; `ua[1]` path 12 Ω of wiring; power-down 0.84 nA.
- **Rule for M2:** a mirror's fingers have the same W and L as its reference (more fingers, not wider ones).

## M2 cells (2026-11-16)

All five analog M2 cells are drawn, Magic DRC 0, KLayout 0 and LVS-matched. Pictures: `material/layout/`.

| Cell | Size (µm) | How |
|---|---|---|
| cap_array | 62.3 × 63.4 | 16 × 16 common-centroid units (each quadrant mirrors one 8 × 8 bit-reversed pattern; every group's centroid is the centre) + a dummy column each side; bottom-plate tracks under the plates; ten group buses below |
| dac_sw_row | 47.1 × 5.7 | full custom: one NMOS and one PMOS stack per bit, shared poly smp/smpb lines |
| comparator | 36.4 × 38.5 | mos_rows, 4 rows: short-L devices in the middle rows; matched pairs mirror-symmetric |
| vcm_gen | 17.5 × 49.5 | mos_rows, narrow (6 rows) for the bottom-right strip |
| inmux | 15.2 × 5.6 | full custom: two NMOS + two PMOS stacks sharing vadc |

**Circuit changes made for the layout** (schematics updated; the ADC-level test reruns on them):
- The switch logic moved into the standard-cell block (`src/sar/sar_drv.v`): dac_sw's NOR/NAND gates,
  inmux's 2-to-4 decoder, the comparator's clock inverter and NAND SR latch (two explicit nand2 cells). The
  analog cells keep only switches, the comparator core and vcm_gen. Ringed transistors for this logic would not
  fit (the dac_sw row alone would have been ~270 µm long).
- DAC unit cap 2 × 2 → 2 × 1.65 µm (≈ 8.0 fF): the bottom-plate via2 must stay 0.1 µm outside the capm and
  bottom plates must be 1.2 µm apart, so 2 × 2 needed a 3.85 µm row pitch. 2 × 1.65 gives a square 3.5 µm pitch.
  No top/bottom dummy rows (height). Extracted routing parasitics: max DNL 0.16, INL 0.12 LSB (all tracks under
  the plates; with tracks in the gaps it was 0.45 LSB).
- vcm_gen: decap 4 → 2 × 8/8 MOS (≈ 1.1 pF); MTOP (top-plate switch) 1 → 2 µm wide and moved into the
  comparator cell (it must sit at the top plate; vcm_gen goes to the bottom right).
- Comparator M3/M4 1 → 2 µm wide (rotated short-L devices need W ≥ 2).

**mos_rows additions** (opt-in; the M1 cells are unchanged): channel track packing (`pack=True`), inner pins on
channel tracks (`inner_pins`), a per-device spacer (`Dev.pre`), and two fixes for short-L devices in middle
rows (gate pad clearance; D/S always up — W = 0.42 devices had their D/S sent down next to the gate stub, a short).

Next: floorplan v4 (the real sizes), adc_digital in LibreLane (now 151 cells, 1430 µm²), M2 top-level
integration, full-chip LVS, post-layout simulation.

## adc_digital (2026-11-16)

`layout/digital/config.json` (LibreLane 3.0.17 in Docker, `librelane --manual-pdk -p sky130A config.json`).
- Die 63.48 × 47.32 µm, routing up to met4 (no met5), PDN: vertical met4 straps only (no core ring); the top
  level ties them to the chip stripes.
- Pins: north = the TT pins in the TT pin order (uo_out, uio_in, ui_in, rst_n, clk); south = switch drivers
  (gn, gpb, smp, smpb, en, enb); east = comparator (smpt, cmp_clkb, opb, onb); west = ref_sel, vref_oe, bg_pd, eoc,
  cmp_out. The 16 constant outputs (uio_oe, uio_out[7:6,3:0]) are tied in metal at the top level.
- Lessons: the repair step's port buffers (57 × clkdlybuf4s25_1, ~500 µm²) made the block unplaceable;
  they are off (`DESIGN_REPAIR_BUFFER_*_PORTS`). The default core margins (4 rows / 12 sites) leave too little
  core in a 63 µm block; they are 1 row / 4 sites.
- Result: route DRC 0, Magic DRC 0, KLayout DRC 0, LVS 0, antenna 0; setup slack +27.4 ns, hold +0.12 ns;
  2 max-slew warnings at ss/100 °C/1.6 V only.

## M2 integration (2026-11-16: DRC and LVS clean)

Floorplan v4 (`layout/floorplan_v4.py`, positions from the real cells; `layout/m2_place.py` builds a
placement-only top and writes every pin's absolute position to `sim/out/layout/m2p/pins.json`).
Right half, bottom to top: vref_buf (M1), vcm_gen (bottom right), `dac` (array + switches, 88.6-153.5 x
64.0-134.05), comparator (rotated, 90.5-130.6 x 134.6-171.0), adc_digital (90.0-153.5 x 171.6-218.9).
The only ways past the array are two corridors: R4 under the middle stripes (x 83-88.4, met2/met3 free)
and R3 under the right stripes (x 153.75-160.7). Routing plan:
- gn/gpb bits 7-4 (west pins) down R4 on met2, met3 jog right at y 56.8-62.4, met4 tracks under the dac
  (over vref_buf, no met4 there; the nearest landing gets the highest track), met4 up to the dac's landing pads.
- gn/gpb bits 3-0, smp, smpb, vin, vptat, vbg, vadc, vcm, pbias down R3 (all met2, ~16 lines at 0.43 pitch;
  horizontals on met3/met4). vptat/vbg run along the very bottom (y 0.5, under the B1 lanes).
- inmux moves to the free area right of the comparator (x 131-153, y 136-160), redrawn with its gate pads
  on top (en/enb straight down from the digital south edge) and its inputs on the right.
- comparator: vtop from the array's met4 spine onto the inp bus (bottom side), vcm onto inn (bottom right),
  pbias/clkb/smpt/opb/onb (top side) short to the digital south pins.
- power: digital straps extended to the block edges -> met3 bars above the block (VDPWR y 219.6, VGND
  y 220.3) to the middle stripes (extended upward); the comparator and the new inmux from extended digital
  straps; vcm_gen and vref_buf from the B1 ties; the dac from the middle stripes (stacks kept out of R4's lines).
- frame: only the 16 constant outputs are tied (uio_oe[5:4] to VDPWR); eoc / cmp_out to uio_out[5:4];
  the 27 north pins river-route to the TT pins above the power bars.
- M1 control signals (BG_PD, VREF_OE, REF_SEL) now come from the digital west pins onto the R1 met4 lines;
  bias_gen's pd is tied to VGND (vcm_gen needs the bias when BG_PD = 1).

**Result (2026-11-16).** `layout/m2_top.py` builds the full tile (`--install` copies it into `gds/`, `lef/`):
Magic DRC 0, KLayout feol/beol/offgrid 0, full-chip LVS "Circuits match uniquely" against
`layout/cells/m2_top_ref.spice` (written by m2_top.py: analog subckts + LibreLane's adc_digital netlist).
Picture: `material/layout/m2_top.png`. Differences from the plan above:
- pbias leaves R3: bias_gen -> x 89.4 (met2, left of the dac) -> the comparator's pbias row and on down to
  y 63.9 -> met3 under the dac to vcm_gen.
- vref: met3 from vref_buf's pin to x 128.5, then met4 up to the dac's vref line (met4 straight from the pin
  shorted to the gn1/gpb1 drops; LVS caught it).
- Slim vias for dense spots (via2 0.32 with a 0.4 × 0.57 met2 / 0.45 met3 pad; via3 0.32 with 0.45 pads),
  north river tracks at 0.8 pitch, en/enb jogs at 0.75 pitch, gn/gpb tracks at y 62.2 − 0.9 k.
- The comparator VGND bus joins the inmux's met4 extension of digital strap 139.74.
- adc_digital is read with `gds readonly true`: Magic's rewrite of the std cells' implant layers failed
  KLayout FEOL (hvtp/nsdm spacing, 21 errors), the verbatim LibreLane GDS is clean.

Next: M2 post-layout simulation (extracted top in the ADC testbench), CI precheck on the pushed GDS.

