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

| vin (V) | ideal floor(256 vin / 1.2143) | sch | rc |
|---|---|---|---|
| 0.050 | 10 (10.54) | 10 | 10 |
| 0.310 | 65 (65.35) | 65 | 65 |
| 0.600 | 126 (126.49) | 127 | 127 |
| 0.900 | 189 (189.74) | 190 | 190 |
| 1.170 | 246 (246.66) | 247 | 247 |

The extracted tile gives the schematic's code at every input. The schematic sits +1 code above floor() at
the three upper inputs (126.49 → 127 etc.); the stage 8 / I3 runs showed the same (reference and switch
details), it is common to both netlists. Run time: 34 min (sch), 51 min (rc) for 5 conversions.

## What this test found (all fixed)

1. **Comparator offset, −40 LSB.** The first rc run read 0 / 25 / 86 / 150 / 207 (sch 10 / 65 / 127 / 190 / 247).
   The extracted comparator alone had a −64 mV offset: 2 fF of layout imbalance on a latch node moved its
   toggle point by 25 to > 80 mV. Fixed in the circuit (xp/xn load caps, longer preamp load) and the layout
   (mirrored buses): `sim/comparator/README.md`.
2. **Comparator / inmux supply through the digital block.** Their VDPWR comes from digital straps 116.84 /
   136.84, which reach the VDPWR stripe only through adc_digital's own power grid (std-cell rails, < 1 Ω
   estimated). The first extraction deleted the block with its straps: the comparator floated, every code 0.
   `m1_pex.py` now keeps the straps and stands in for the grid with a met3 bar. In the real layout this path is
   LVS-clean; a direct strap-to-stripe tie would be more robust (optional, before the freeze).
3. **Simulator settings.** `sim/m2` had no `.spiceinit` (sky130 compatibility mode, one thread): the runs took
   > 2 h for one conversion. With it, the first clock edge failed with "timestep too small" in an xhigh_po
   resistor (its R depends on abs(V), a kink at 0 V): `.options rshunt=1e12` (1 TΩ per node, ~1 pA) fixes it.
   Settings: `reltol=1e-5 abstol=1e-12 vntol=1e-6 method=gear rshunt=1e12`.
