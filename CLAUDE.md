# Project rules — TTSKY26d analog: bandgap-referenced 8-bit SAR ADC + temperature sensor

Tiny Tapeout analog project on SkyWater sky130. Top module: `tt_um_chiranjitpatel_sar_adc`.
**Fixed budget: 1x2 tile, 2 analog pins (`ua[0]`, `ua[1]`), VDPWR only.** It's already purchased; don't grow it.
Specs live in `docs/specs/`. Read them before changing any circuit.

## Tool flow (keep to this flow)

| Step | Tool | Notes |
|---|---|---|
| Schematic | xschem | Schematics are the source of truth for the circuit |
| Pre-layout sim | ngspice | Batch mode, scripted testbenches; netlist exported from xschem |
| Layout | KLayout | Hand layout and Python (`klayout` package) generated structures |
| DRC | KLayout sky130 deck + Magic DRC | Both must be clean; TT precheck runs both |
| Extraction / LVS | Magic (read GDS → extract) + netgen | Same flow as the TRNG project |
| Post-layout sim | ngspice | Same testbenches, extracted netlist swapped in |
| Sign-off | GitHub Actions `gds.yaml` (TT precheck) | Must pass before submission |

TT precheck uses **KLayout 0.30.4** and **Magic 8.3.568** (`tt-support-tools/precheck/tool-versions.json`).
Use these versions for local DRC; the Ubuntu apt packages are older.

## Simulation policy

- **Phase 1 (now):** a single operating point — `tt` corner, 27 °C, VDPWR = 1.80 V.
  Every block must meet its spec here before moving on.
- **Phase 2 (before layout freeze):** corners `tt/ff/ss/fs/sf`, temperature −40/27/125 °C,
  supply 1.62/1.80/1.98 V, plus Monte Carlo mismatch on matched structures
  (comparator input pair, cap DAC, bandgap core).
- **Phase 3:** repeat the key tests on the extracted (post-layout) netlist.
- Every spec number in `docs/specs/` has a testbench that measures it. Record results in the
  spec's "Status" table, with the phase it was measured in.

## Design rules

1. Keep scope small and stay within the area budget in `docs/specs/top_level.md`. The ADC must
   also work with an external reference on `ua[1]`, so a bandgap failure doesn't kill the ADC.
   If the design doesn't fit, cut in the order listed in the spec. Resolution is the last thing to cut.
2. Analog pads are slow and lossy (series resistance and pad capacitance — check the current
   numbers on the TT analog specs page). Never connect a fast or high-impedance node directly to a pad.
3. Every function must be observable on the digital pins (codes, flags, comparator output),
   so it can be tested from the TT demo board's RP2040 without lab equipment.
4. Provide bypass and debug modes on digital inputs: external SAR control, an analog debug
   mux, enable/power-down for each block.
5. Comparator kickback and DAC top-plate coupling must be checked in simulation; shield the
   top-plate routing (lesson from TT06 silicon, see `docs/specs/prior_art.md`).
6. Matched devices: common-centroid or interdigitated, with dummies, the same orientation, and guard rings.
7. Every node that can start in a bad state (bandgap, biasing) needs a startup circuit,
   and a transient testbench that proves it starts from 0 V.
8. Layout is frozen 3 weeks before the shuttle deadline; the remaining time is for DRC/LVS/precheck only.
9. `docs/info.md` must contain the full test procedure before tapeout.

## Repository layout (create as needed)

```
docs/specs/      block specifications (this is the contract)
xschem/          schematics + symbols (.sch/.sym)
sim/             ngspice testbenches, run scripts, results summaries
layout/          GDS, KLayout Python generators, DRC/LVS scripts
src/project.v    blackbox Verilog for the TT top module (pins only)
```

## Conventions

- Device names: use sky130 primitives (`sky130_fd_pr__nfet_01v8`, `__pfet_01v8`,
  `__pnp_05v5_W3p40L3p40`, `__res_xhigh_po_*`, `__cap_mim_m3_1`, ...).
- Net names: `VDPWR`, `VGND`, `vin`, `vref`, `vbg`, `d[7:0]`, lower-case for internal nets.
- No generated junk in git: simulation raw files, `*.ext`, `*.log` go under `sim/out/` (ignored).
