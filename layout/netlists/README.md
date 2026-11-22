# Top-level netlists of tt_um_chiranjitpatel_sar_adc

Snapshots for review and LVS on another machine (2026-11-22, from the submission GDS `gds/tt_um_chiranjitpatel_sar_adc.gds`).
The generating scripts are the source of truth; re-create these files with the commands below after any change.

| File | What | Made by |
|---|---|---|
| `tt_um_chiranjitpatel_sar_adc.sch.spice` | **Pre-layout / LVS reference**: the xschem netlists of the analog blocks + LibreLane's gate-level `adc_digital`, wired as in the top level | `python3 layout/m2_top.py` (writes `layout/cells/m2_top_ref.spice`; this is a copy) |
| `tt_um_chiranjitpatel_sar_adc.lvs.spice` | **Layout netlist for LVS**: Magic extraction of the GDS (`ext2spice lvs`, devices only, hierarchical, std cells as subcircuits) | `python3 layout/check_cell.py tt_um_chiranjitpatel_sar_adc --gds gds/tt_um_chiranjitpatel_sar_adc.gds --netlist layout/cells/m2_top_ref.spice` (→ `sim/out/layout/tt_um_chiranjitpatel_sar_adc/`) |
| `tt_um_chiranjitpatel_sar_adc.rc.spice` | **Post-layout netlist for simulation**: flat R + C extraction (Magic 8.3.623 `extresist`, C ≥ 0.01 fF) of everything except `adc_digital`, which is instanced from `layout/digital/adc_digital.spice` | `python3 layout/m1_pex.py m2` (→ `sim/out/layout/m2_rc/m2_rc.spice`; this is a copy with a relative include) |

## LVS at your end (netgen)

    netgen -batch lvs "tt_um_chiranjitpatel_sar_adc.lvs.spice tt_um_chiranjitpatel_sar_adc" \
                      "tt_um_chiranjitpatel_sar_adc.sch.spice tt_um_chiranjitpatel_sar_adc" \
                      $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs_report.txt

Expected: `Circuits match uniquely` (76 nets, 11 top-level subcircuit instances). netgen lists `ena`, `ua[2]` … `ua[7]`
as disconnected top-level pins and `uio_in[4]`, `uio_in[5]` as unused `adc_digital` ports; both are expected.

To extract the layout netlist yourself instead of using the `.lvs.spice` snapshot, read the GDS in Magic with the
sky130A rc file and run the same commands as `layout/check_cell.py` (`gds flatglob *__example_*`, `gds read`,
`extract do local`, `extract all`, `ext2spice lvs`, `ext2spice`). Read `adc_digital` with `gds readonly true` only if
you write the GDS back out (see `docs/specs/layout_plan.md`); for extraction it doesn't matter.

## Paths to adjust

- `*.sch.spice` line 2 includes the std-cell library from `/usr/local/share/pdk/sky130A/...`: point it at your
  `$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice`.
- `*.rc.spice` includes `../digital/adc_digital.spice` relative to this folder; for ngspice also include the std-cell
  library above and the device models (`.lib $PDK_ROOT/sky130A/libs.tech/ngspice/sky130.lib.spice tt`). The whole-tile
  testbenches in `sim/m2/` (`make_tb.py`, `scenarios.py`) show the full setup, including the simulator options.
