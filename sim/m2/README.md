# M2 post-layout simulation: the whole tile

Full conversions on `tt_um_chiranjitpatel_sar_adc`, driven only through its pins (as from the TT demo board).
tt corner, 27 °C, VDPWR 1.8 V (Phase 3 key test, `CLAUDE.md`).

| File | What |
|---|---|
| `make_tb.py [vin ...]` | writes `tb_m2_sch.spice` and `tb_m2_rc.spice` (default 5 inputs, 0.05–1.17 V) |
| `decode.py` | decodes the codes 0.2 µs after each EOC rise, writes `results.md` |
| `results.md` | schematic vs extracted vs ideal codes |

Netlists:
- **sch**: `layout/cells/m2_top_ref.spice` (written by `layout/m2_top.py`: the xschem analog subckts + LibreLane's
  `adc_digital` gate-level netlist, the same netlist LVS uses).
- **rc**: `python3 layout/m1_pex.py m2` → `sim/out/layout/m2_rc/m2_rc.spice`. Flat R+C of everything except
  `adc_digital` (3258 R, 2858 C). The digital block is instanced from its LibreLane netlist on the extracted pin
  nets (its timing is signed off by LibreLane STA); its met4 power straps stay in the extraction, because the
  comparator and the inmux take VDPWR through them.

Setup: internal reference (BG_PD = VREF_OE = REF_SEL = 0), INSEL = 0 (ua[0]), clk 1 MHz, START high, one
conversion every 10 µs from 3 µs (the transient starts from the operating point, so the reference is settled;
startup is covered in `sim/m1`). Pad models from `CLAUDE.md` rule 2 on ua[0] and ua[1] (ua[1] with a DMM load).

## Result (2026-11-16, comparator F2)

| vin (V) | ideal floor(256 vin / 1.2078) | sch | rc |
|---|---|---|---|
| 0.050 | 10 (10.60) | 10 | 10 |
| 0.310 | 65 (65.71) | 65 | 65 |
| 0.600 | 127 (127.17) | 127 | 127 |
| 0.900 | 190 (190.74) | 190 | 190 |
| 1.170 | 247 (247.98) | 247 | 247 |

The extracted tile gives the schematic's code at every input, and both are the ideal code for the tile's own
VREF (1.2078 V, measured on ua[1] in the `gnd` scenario below; I3 had 1.2143 V). Run time: 34 min (sch),
51 min (rc) for 5 conversions.

## I4 operating scenarios (2026-11-21, schematic netlist)

`scenarios.py` (all settings from `docs/specs/top_level.md`, pins only) → `scenarios.md`:

| Scenario | Result |
|---|---|
| VGND input + VREF on ua[1] (DMM) | code 0; ua[1] = 1.2078 V DC (dips of up to 35 mV for ~100 ns while the DAC switches) |
| Temperature sensor, 100 kHz | 127 (expected 127.0 for VPTAT 0.599 V) |
| Bandgap via ADC, 1.5 V on ua[1], 100 kHz | 206 → VBG ≈ 1.208 V |
| Bandgap fallback, BG_PD = 1, 1.5 V on ua[1] | 102, 199 = floor(256 vin / 1.5) |
| External SAR (MODE = 1) | CMP_OUT 0 / 0 / 0 / 1 for trial codes 120 / 126 / 127 / 133 (vin = code 127.2); D mirrors EXT_D |

## What this test found (all fixed)

1. **Comparator offset, −40 LSB.** The first rc run read 0 / 25 / 86 / 150 / 207 (sch 10 / 65 / 127 / 190 / 247).
   The extracted comparator alone had a −64 mV offset: 2 fF of layout imbalance on a latch node moved its
   toggle point by 25 to > 80 mV. Fixed in the circuit (xp/xn load caps, longer preamp load) and the layout
   (mirrored buses): `sim/comparator/README.md`.
2. **Comparator / inmux supply through the digital block.** Their VDPWR comes from digital straps 116.84 /
   136.84, which reach the VDPWR stripe only through adc_digital's own power grid (std-cell rails, < 1 Ω
   estimated). The first extraction deleted the block with its straps: the comparator floated, every code 0.
   `m1_pex.py` now keeps the straps and stands in for the grid with a met3 bar. Since 2026-11-21 the layout also
   ties both straps to the stripe directly (a met4 bar below adc_digital).
3. **Simulator settings.** `sim/m2` had no `.spiceinit` (sky130 compatibility mode, one thread): the runs took
   > 2 h for one conversion. With it, the first clock edge failed with "timestep too small" in an xhigh_po
   resistor (its R depends on abs(V), a kink at 0 V): `.options rshunt=1e12` (1 TΩ per node, ~1 pA) fixes it.
   Settings: `reltol=1e-5 abstol=1e-12 vntol=1e-6 method=gear rshunt=1e12`.
