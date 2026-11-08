# Layout plan — milestones and chunks

**Status: DRAFT (2026-11-08).** Deadline: **TTSKY26d, 2026-12-01.**
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
| 1a | bias_gen | designer | Nov 11 |
| 1b | ota | designer | Nov 12 |
| 1c | PNP 3×3 common-centroid array + R1/R2 unit-resistor chains (scripted) | Claude | Nov 11 |
| 1d | bandgap_core assembly (1b + 1c + current sources + startup) | designer, Claude checks | Nov 13–14 |
| 1e | ptat_out (one PMOS + resistor chain) | Claude | Nov 14 |
| 1f | vref_filt (resistor chain + MOS cap, scripted) | Claude | Nov 14 |
| 1g | vref_buf + reservoir cap | designer | Nov 15 |
| 1h | vref_sel logic + `ua[1]` transmission gate | designer | Nov 16 |
| **M1** | Integration, LVS, post-layout sim, precheck | Claude | **Nov 17** |
| 2a | DAC unit cell + 16 × 16 common-centroid MIM array (scripted) | Claude | Nov 18 |
| 2b | dac_sw (one cell, used 9×) | designer | Nov 18 |
| 2c | comparator (with preamp) | designer | Nov 19–20 |
| 2d | vcm_gen + top-plate switch | designer | Nov 20 |
| 2e | inmux | designer | Nov 21 |
| 2f | adc_digital place & route (LibreLane / OpenROAD, sky130_fd_sc_hd) | Claude | Nov 18–21 |
| **M2** | Integration, LVS, post-layout sim, precheck | both | **Nov 24–26** |
| — | Freeze; final checks; submission | both | Nov 26 – Dec 1 |

In parallel (Claude): Phase 2 block sweeps (before each cell), I4 full-chip simulation, post-layout
simulation of each cell as it is finished.

## Tools

- Layout: KLayout (designer's 0.30.8; precheck uses 0.30.4). Extraction/LVS: Magic + netgen.
- Digital P&R: LibreLane in Docker (`ghcr.io/librelane/librelane:3.0.17`). Nix's LibreLane binary
  cache (librelane.cachix.org) is blocked by this environment's network policy; Docker works.
