# Integration I2/I3 — full ADC at transistor level (adc_core)

Schematic: `xschem/adc_core.sch` (`xschem/gen_adc_core.py`): cap_dac + comparator (with preamp) +
vcm_gen + sar_logic (Yosys → `tools/gl2spice.py` → sky130_fd_sc_hd SPICE cells).

| Script | What |
|---|---|
| `make_tb.py [--real-ref] [--debug] name vin…` / `--sine N M amp offset` | builds `tb_<name>.spice` (I2: ideal VREF; I3: bandgap → filter → buffer) |
| `decode.py name` | reads D[7:0] 0.2 µs after each EOC and compares with floor(256·VIN/VREF) |
| `run_long.sh` | I3 quick, I2 code-edge test, I2 64-point sine, in parallel |

**In this cloud session**, processes detached with `nohup setsid` were killed a few minutes after the
turn ended (twice). Run long jobs as tool background tasks instead (2 h limit): split them into pieces
(`edges_a/_b`, sine in chunks) that each finish within 2 h.

Speed: ≈ 1–4 µs of simulated time per minute (≈ 1700 transistors incl. the std cells, reltol 1e-5),
i.e. ~3–10 minutes per conversion.

## Bugs found by this integration step (both fixed)

1. **Glitch on `smpt` (SAR logic):** see `src/sar/README.md`. The top-plate switch re-closed for a gate
   delay just as the bottom plates switched, and the codes were wrong.
2. **Comparator kickback asymmetry:** constant −2 LSB offset. The fix is a continuous-time preamp,
   see `sim/comparator/README.md`.

Also two testbench bugs: the VIN PWL ramped between values (now held), and the decoder read the bus a
fixed number of *samples* after EOC (adaptive timestep → wrong time; now 0.2 µs after EOC).

## Results (tt, 27 °C, 1.8 V)

| Test | Result |
|---|---|
| I2, ideal VREF, 5 inputs (0.1 / 0.3 / 0.6 / 0.9 / 1.15 V) | codes 21 / 63 / 126 / 189 / 242 = ideal, **error 0** |
| I3, real reference chain, same inputs | running |
| I2, code edges ±0.2 LSB around 1, 32, 63/64, 127/128, 191/192, 254 | running |
| I2, 64-point coherent sine (7 cycles) | running (SNDR/ENOB) |
