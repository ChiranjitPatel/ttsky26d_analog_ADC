# Project rules — TTSKY26d analog: bandgap-referenced 8-bit SAR ADC + temperature sensor

Tiny Tapeout analog project on SkyWater sky130. Top module: `tt_um_chiranjitpatel_sar_adc`.
**Fixed budget: 1x2 tile, 2 analog pins (`ua[0]`, `ua[1]`), VDPWR only.** It's already purchased; don't grow it.
Specs live in `docs/specs/`. Read them before changing any circuit.
Work follows the bottom-up stage plan in `docs/specs/stage_plan.md`: one block per stage,
integration one proven block at a time. Update its Status table as stages finish.

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
- **Simulator accuracy (learned in stages 6–8):**
  - Precision transients (anything judged against the LSB, 4.75 mV) need
    `.options reltol=1e-5 abstol=1e-14 vntol=1e-8 chgtol=1e-17`. The default reltol (1e-3)
    lets node voltages wander by ~1 mV.
  - Comparator decisions: with the default reltol, 1 mV decisions came out wrong in ~10 % of
    cycles. reltol 1e-5 fixes it and lets the adaptive step do the work (32 s for 12 µs). A forced
    5 ps max step also works, but is 10× slower.
  - Use `set num_threads=1` in `.spiceinit`. With 4 threads, parallel runs oversubscribe the CPU
    and slow down ~15× (OpenMP spin-waits).
  - In long fine-step runs, `save` only the needed vectors (saving everything used 1.7 GB per run).
- Every spec number in `docs/specs/` has a testbench that measures it. Record results in the
  spec's "Status" table, with the phase it was measured in.

## Design rules

1. Keep scope small and stay within the area budget in `docs/specs/top_level.md`. The ADC must
   also work with an external reference on `ua[1]`, so a bandgap failure doesn't kill the ADC.
   If the design doesn't fit, cut in the order listed in the spec. Resolution is the last thing to cut.
2. Analog pads are slow and lossy: R < 500 Ω, C < 5 pF, max 4 mA, through the TT analog switch
   (tinytapeout.com/specs/analog). Model this in every testbench that touches `ua[]`.
   Never connect a fast or high-impedance node directly to a pad.
3. Every function must be observable on the digital pins (codes, flags, comparator output),
   so it can be tested from the TT demo board's RP2040 without lab equipment.
4. Provide bypass and debug modes on digital inputs: external SAR control, internal nodes
   readable through the ADC input mux, enable/power-down for each block.
5. Comparator kickback and DAC top-plate coupling must be checked in simulation; shield the
   top-plate routing (lesson from TT06 silicon, see `docs/specs/prior_art.md`).
6. Matched devices: common-centroid or interdigitated, with dummies, the same orientation, and guard rings.
7. Every node that can start in a bad state (bandgap, biasing) needs a startup circuit,
   and a transient testbench that proves it starts from 0 V.
8. Layout is frozen 3 weeks before the shuttle deadline; the remaining time is for DRC/LVS/precheck only.
9. `docs/info.md` must contain the full test procedure before tapeout.
10. **No met5** anywhere (TT power grid). Power = vertical met4 stripes ≥ 1.2 µm wide, from the bottom
    10 µm to the top 10 µm of the tile. Tie all unused digital outputs to VGND.

## Repository layout (create as needed)

```
docs/specs/      block specifications (this is the contract)
xschem/          schematics + symbols (.sch/.sym)
sim/             ngspice testbenches, run scripts, results summaries
layout/          GDS, KLayout Python generators, DRC/LVS scripts
material/        explanatory images and drawings for the designer, in topic subfolders (see material/README.md)
src/project.v    blackbox Verilog for the TT top module (pins only)
```

## Conventions

- Device names: use sky130 primitives (`sky130_fd_pr__nfet_01v8`, `__pfet_01v8`,
  `__pnp_05v5_W3p40L3p40`, `__res_xhigh_po_*`, `__cap_mim_m3_1`, ...).
- Net names: `VDPWR`, `VGND`, `vin`, `vref`, `vbg`, `d[7:0]`, lower-case for internal nets.
- No generated junk in git: simulation raw files, `*.ext`, `*.log` go under `sim/out/` (ignored).
