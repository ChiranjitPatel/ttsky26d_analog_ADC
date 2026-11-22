# Scripted cells (chunks 1c, 1e, 1f) — how to use them

**Status: 2026-11-08 (night).** All four cells come from Python generators that drive Magic and the PDK device
generators, so you never edit them by hand: change the generator and run it again. Each one is
**Magic DRC 0, KLayout DRC 0** (TT precheck deck: feol, beol, offgrid) **and LVS match**.

| Cell | Generator | GDS | Size (µm) | Contents |
|---|---|---|---|---|
| `pnp_array` | `layout/gen_pnp_array.py` | `layout/cells/pnp_array.gds` | 28.7 × 22.3 | bandgap PNPs: Q1 ×1, Q2 ×8 (common centroid), Q3 ×1, 2 dummies |
| `bg_res` | `layout/gen_bg_res.py` | `layout/cells/bg_res.gds` | 21.2 × 13.3 | bandgap R1 (2 units) + R2 (19 units) interdigitated, 2 dummies |
| `ptat_out` | `layout/gen_ptat_out.py` | `layout/cells/ptat_out.gds` | 23.0 × 21.4 | MPP pfet 8/4 + R3 (22 units), 2 dummies — the complete block |
| `vref_filt` | `layout/gen_vref_filt.py` | `layout/cells/vref_filt.gds` | 49.4 × 27.4 | RF 9 × 0.35/20 + MCF 5 × nfet 10/10 — the complete block |

`ptat_out` and `vref_filt` are complete blocks (their outline fits the floorplan: 28 × 26 and 54 × 34 µm).
`pnp_array` and `bg_res` are parts of `bandgap_core` (chunk 1d): place them next to the OTA and the current
sources in your assembly.

## Pins (cell coordinates, µm; label centre)

| Cell | Pin | Layer | Position |
|---|---|---|---|
| pnp_array | va (Q1 emitter) | met3 | (9.79, 20.28), top |
| | vq2 (Q2 emitters) | met2 | (−0.70, 9.79), left |
| | vq3 (Q3 emitter) | met3 | (26.72, 9.79), right |
| | VGND | met1 | bar along the bottom, y = −0.90 |
| bg_res | vbg (R2 start) | met2 | (1.57, −2.35), bottom |
| | vb (R1 start) | met3 | (5.72, −2.35), bottom |
| | vq2 (R1 end) | met3 | (14.02, −2.35), bottom |
| | vq3 (R2 end) | met2 | (18.17, 10.60), top |
| | VGND | met1 | left bar, (−0.60, 3.70) |
| ptat_out | vgp | met2 | (3.98, 20.00), top |
| | vptat | met2 | (−1.24, −0.64), bottom left |
| | VDPWR | met1 | (7.09, 14.28), right of the PMOS |
| | VGND | met1 | left bar, (−0.34, 3.97) |
| vref_filt | vbg | met2 | (1.83, −0.94), bottom left |
| | vbg_f | met2 | (44.41, 24.32), top right |
| | VGND | met1 | left bar, (−0.34, 12.96) |

Routing inside the cells uses li1, met1, met2 and (pnp_array, bg_res) met3. **Don't route met3 across
`pnp_array` or `bg_res`.** met4 is free everywhere.

## Matching

- **pnp_array:** Q1 sits in the centre of the 3 × 3 and the eight Q2 around it, so both have the same centroid.
  Q3 and two dummies form a fourth column. Each PDK PNP cell has its own base and collector rings, and
  neighbouring collector rings merge.
- **bg_res:** R1 is at positions 5 and 15 of 21 active strips, and R2 fills the rest. Both centroids are at
  position 10, so a linear gradient doesn't change R2/R1. There is one dummy strip at each end, inside a common
  guard ring.
- The resistor generator's `l` includes the contact overlap. l = 2.16 extracts as L = 2.00, which is the value in
  the schematic and the model.

## Checks (run after any change)

```bash
python3 layout/gen_pnp_array.py
```

```bash
python3 layout/check_cell.py pnp_array --netlist layout/cells/pnp_array_ref.spice
```

```bash
python3 layout/klayout_drc.py layout/cells/pnp_array.gds
```

Use the same three commands for `bg_res` (with `--netlist layout/cells/bg_res_ref.spice`). `ptat_out` and
`vref_filt` check directly against their schematic netlists (no `--netlist`).
`klayout_drc.py` needs the Docker daemon (`dockerd &`), because KLayout runs in the LibreLane container.

## Fixes to the checker found on the way (2026-11-08)

The Magic DRC count in `check_cell.py` (and in the generators and `m0_frame.py`) had two holes. A deliberately
too-thin met1 wire (0.10 µm) was reported as 0 errors:
1. `drc list count total` returned 0 while `drc listall why` listed errors. The count now comes from the list.
2. Magic marks an error as the region where the rule fails, and that region can lie outside the cell's
   bounding box. `drc listall` only returns errors inside the box, so the box is now grown by 5 µm first.

After the fix the test wire gives 1 error (and KLayout reports `MR_met1.WID.1` for it). All cells and the M0 frame
were re-checked and are clean. Your `bias_gen` check will use the fixed version.
