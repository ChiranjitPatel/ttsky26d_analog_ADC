# Stage 9 — SAR logic (`sar_logic`)

The digital part of the ADC is written in Verilog (this is its source of truth; it's synthesized to
sky130_fd_sc_hd standard cells and placed as a block inside the analog layout).

| File | What |
|---|---|
| `sar_logic.v` | RTL: sequencer, successive-approximation register, external-mode multiplexing |
| `synth.ys` | Yosys script → `sim/out/sar/sar_logic_gl.v` (gate-level netlist) |
| `../../test/sar/tb_sar.v` | Testbench with a behavioural DAC + comparator model |
| `../../tools/filter_liberty.py` | Removes cells we never want from synthesis (lpflow isolation, probes, taps, `_0` sizes) |

Run (from the repository root):
```
mkdir -p sim/out/sar
python3 tools/filter_liberty.py $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib sim/out/sar/hd_tt_filtered.lib
yosys -q -l sim/out/sar/synth.log src/sar/synth.ys
iverilog -g2012 -o sim/out/sar/rtl.vvp src/sar/sar_logic.v test/sar/tb_sar.v && vvp -n sim/out/sar/rtl.vvp
V=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o sim/out/sar/gl.vvp $V/primitives.v $V/sky130_fd_sc_hd.v sim/out/sar/sar_logic_gl.v test/sar/tb_sar.v && vvp -n sim/out/sar/gl.vvp
```

## Timing (internal mode, `mode` = 0; 10 clocks per conversion)

| Clock | smp | smpt | b[7:0] | cmp_clk | Notes |
|---|---|---|---|---|---|
| SAMPLE | 1 | 1, falls at the falling edge (negedge flip-flop) | 0 | 0 | top plate opens at the falling edge = sampling instant |
| BIT7 … BIT0 | 0 | 0 | trial code | ~clk | DAC settles while clk high, comparator decides while clk low; bit kept if q = 0 |
| EOC | 1 | 0, rises at the falling edge | 0 | 0 | d[7:0] loaded, eoc = 1; next SAMPLE if `start` is still high |

External mode (`mode` = 1): b = ext_d, smp = smpt = ext_sample, cmp_clk = ext_cmp_clk, d = ext_d, eoc = 0.
In external mode the top and bottom plates open together, so sampling has a small input-dependent
charge-injection error. That's acceptable for a debug path.

## Bug found in integration (I2): glitch on smpt

The first version made `smpt` combinationally (`tracking & ~(SAMPLE & ~clk)`). On the rising edge that
ends SAMPLE, `clk` rises a gate delay before the state register leaves SAMPLE, so `smpt` glitched
high. That briefly reconnected the top plate to vcm while the bottom plates switched, which re-sampled
and gave wrong codes in the transistor-level ADC run. The zero-delay RTL test can't see this. Fix:
`smpt` is a falling-edge flip-flop. `tb_sar.v` now also checks that `smpt` falls exactly once per
conversion: the old gate-level netlist fails that check in every conversion, the fixed one passes.

## Results (2026-11-07)

- RTL (after the smpt fix): 2764 conversions (all code centres, all code edges ± 0.01 LSB, ~2000 random inputs) → **0 errors**;
  10 clocks per conversion; external-mode pass-through correct.
- Synthesis (tt_025C_1v80, filtered liberty): **120 cells, 1254 µm²** cell area (≈ 1700 µm² placed at
  ~70 % density) — inside the 4000 µm² budget for SAR logic + control.
- Gate-level simulation (sky130 functional models, unit delay): same testbench → **0 errors, 0 smpt glitches**.
- Transistor-level check (std-cell SPICE models with the real analog blocks) is part of integration stage I2.
