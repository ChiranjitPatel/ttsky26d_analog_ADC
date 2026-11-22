# M1 post-layout simulation (Phase 3 for the reference chip)

The same testbenches run on two netlists of the M1 top level `tt_um_chiranjitpatel_sar_adc`:
- **sch:** the schematic top level `layout/cells/m1_top_ref.spice`, written by `layout/m1_top.py` from the xschem
  netlists.
- **rc:** the flat R+C extraction of the submission GDS `gds/tt_um_chiranjitpatel_sar_adc.gds`, written by
  `layout/m1_pex.py` to `sim/out/layout/m1_rc/m1_rc.spice`.

The DUT is driven only through its pins, as on the TT demo board: `ui_in[3]` BG_PD, `ui_in[1]` VREF_OE,
`uio_in[3]` REF_SEL, `ua[1]` VREF pad. The pad model is 5 pF on the chip side and 500 Ω to the pin, with a
10 MΩ ∥ 10 pF DMM on the pin. Unused pins get 1 GΩ to ground so no node floats.

| File | What |
|---|---|
| `make_tb.py` | writes `tb_m1_{sch,rc}_{op,ac,tran}.spice` |
| `run.sh` | extract (`--no-extract` skips it), write the testbenches, run all six in parallel, report |
| `report.py` | `results.md` + `plots/m1_postlayout.png` |
| `corners_b7.py` | B7 over 5 process × 3 temperatures × 3 supplies on both netlists → `corners_b7.md` |

The tests:
- **op:** four modes (internal, DMM readout, external reference, BG_PD).
- **ac:** PSRR at `vbg`, `vbg_f` and `vref`.
- **tran:** startup from 0 V with a 1 µs ramp; VREF_OE = 1 from 150 µs; BG_PD from 250 to 300 µs, then restart.

## Extraction (`layout/m1_pex.py`)

- Magic flattens the top cell, extracts it, runs `extresist all` and writes `ext2spice` with R and C.
  Coupling caps are kept down to 0.01 fF.
- VDPWR/VGND and the VGND-tied outputs are not resistance-extracted. Their currents are µA, so the IR drop is µV.
- It runs **Magic 8.3.623 from the LibreLane Docker image.** The local Magic 8.3.411 runs `extresist` but its
  `ext2spice` drops every resistor. It also needs `select top cell` after loading the flattened cell, and a Tcl
  list for port names with brackets (`extresist ignore {uo_out[0]}`).
- The newer Magic reports xhigh_po resistor lengths 0.11–0.16 µm longer than drawn (4.16 instead of 4). The
  netlist is used as extracted. A run with the drawn lengths restored differs by < 0.2 dB in PSRR and 1 mV in VBG.
- Pin-to-device resistance (`sim/out/m1/extract.txt`): `ua[1]` 12 Ω (pad budget 500 Ω); the control pins
  10–60 Ω.

## Results

See `results.md` (tt, 27 °C, 1.8 V) and `corners_b7.md` (B7 over corners). Every value is within 1 mV or 1 dB
of the schematic, and all targets are met.

## Findings (2026-11-14)

1. **Current mirrors drawn with wider fingers than their reference mirrored the wrong current.**
   - LVS can't see this: it merges parallel devices, so 1 × 8/2 and 4 × 2/2 compare as equal.
   - sky130's narrow-width effect does see it: a 2 µm-wide reference has a higher Vth per µm than a 4–10 µm
     finger.
   - Measured in the extracted netlist:
     - vref_buf tail (2 × 10/2 against a 2/2 reference): 12.3 µA instead of 9.6 µA.
     - OTA tail M5 (1 × 4/2): 1.68 µA instead of 1.9 µA.
     - OTA output M7 (1 × 8/2): 3.06 µA instead of 3.8 µA.
   - The lower OTA bias cost 1.4 dB of B7 at 1 MHz.
   - Fixes:
     - bandgap_core draws M5 as 2 × 2/2 (row 1) and M7 as 4 × 2/2 (row 2). The cell is still 71.7 × 104 µm.
     - vref_buf's tail is now 2 × 8/2 in both the schematic and the layout (9.6 µA, as designed).
   - The standalone `ota.gds` (not on the chip) still has the merged M5/M7.
2. **B7 at 1 MHz missed in hot / fs corners, already in the schematic** (worst 19.5 dB schematic, 19.0 dB layout,
   at fs / 125 °C / 1.62 V). The earlier "≥ 20.3 dB in every corner" came from the block-level corner runs.
   - Fix: a MIM cap CM = 2 × (21 × 30 µm) ≈ 2.5 pF from `vbg_f` to VGND, stacked over vref_filt's resistor
     chain and MOS caps.
   - That cell used only met1/met2, so the cap costs no area. The top plate is `vbg_f` (met4), the bottom plate
     is VGND (met3).
   - Result: +3.4 dB (tt 24.5 dB schematic / 23.8 dB layout).
   - Side effect: startup to 1 % takes 24 µs instead of 15 µs (target ≤ 100 µs).
3. **Parasitics are small.**
   - The largest couplings on the reference nets are a few fF:
     - `vbg_f`: 0.8 fF to VDPWR, 1.6 fF to `ua[1]`.
     - `vref`: 15 fF to `ua[1]`, 8 fF to VDPWR.
   - All of these sit against pF-level filter and reservoir caps.
   - `vgp` carries ~220 fF to ground (MIM bottom plate + its route to ptat_out). Adding that to the schematic
     changes B7 by 0.1 dB.
4. **Floating pins:** the extracted top level has the unused analog pads as real nodes. Left open, ngspice gets a
   singular matrix and lands in a wrong operating point (VBG 0.85 V). The testbench ties them to ground with 1 GΩ.
