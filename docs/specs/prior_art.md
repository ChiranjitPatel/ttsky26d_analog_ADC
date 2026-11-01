# Prior art — Tiny Tapeout SAR ADCs and bandgaps (surveyed 2026-11-01)

The survey covered GitHub repo search and web search. tinytapeout.com wasn't reachable at survey
time, so the list may be incomplete.

## SAR ADCs

| Project | Shuttle | Summary | Result |
|---|---|---|---|
| [wulffern/tt06-sar](https://github.com/wulffern/tt06-sar) | TT06 | 8-bit SAR, 1x2, MIM caps | **Works in silicon**: noise < 1.5 LSB, ~7 ENOB full-scale. Harmonics attributed to interference/kickback |
| [rnunes2311/tt07-12bit_SAR_ADC](https://github.com/rnunes2311/tt07-12bit_SAR_ADC) | TT07 | 12-bit, preamp + StrongARM, 1x2, 5 analog pins | Notes that the TT analog mux adds distortion |
| [mthudaaa/tt08_epc_sar_adc](https://github.com/mthudaaa/tt08_epc_sar_adc) | TT08 | SAR | — |
| [davidbroughsmyth/12-bit_sar_adc_ttsky26c](https://github.com/davidbroughsmyth/12-bit_sar_adc_ttsky26c) | 26c | 12-bit, R-2R DAC, 2x2 | — |
| [KavishkaJayakody/ttsky26c_ns_sar_adc](https://github.com/KavishkaJayakody/ttsky26c_ns_sar_adc) | 26c | Noise-shaping SAR, 2x2, 6 pins | — |
| [ShrihariNarayan/ttsky26d-sar-adc](https://github.com/ShrihariNarayan/ttsky26d-sar-adc) | **26d** | 8-bit, 1x2, 2 pins, 256 × 2 µm MIM, bootstrapped switch, StrongARM, 1 MS/s | Same shuttle — shows that 8-bit fits in 1x2 |
| [ishi-kai/ttsky26d-tt_um_ISHIKAI_SARADC](https://github.com/ishi-kai/ttsky26d-tt_um_ISHIKAI_SARADC) | 26d | 6-bit workshop sample | — |

## Bandgaps

| Project | Shuttle | Summary |
|---|---|---|
| tt_um_bgr_agolmanesh | TT08 | 1.2 V target, 1.8 V supply |
| tt_um_cw_vref | ttcad25a | Current-mode, 3.3 V supply |
| [RamonSsc/tt_um_Onchip_BandGap](https://github.com/RamonSsc/tt_um_Onchip_BandGap), […_Trimmed_BandGap](https://github.com/RamonSsc/tt_um_Onchip_Trimmed_BandGap) | 2025–26 | 1.2 V, 3-bit resistor trim |
| [kovistvan/tt_um_ik_0_ptat_bgr_ieee](https://github.com/kovistvan/tt_um_ik_0_ptat_bgr_ieee) | 2026 | Pseudo-PTAT cells, 48 ppm/°C (sim), 1 pin |
| [wecallemjazzyfact/TinyTapeout-BGR-LDO](https://github.com/wecallemjazzyfact/TinyTapeout-BGR-LDO) | 26c | BGR + LDO, 6-bit trim, VAPWR |

No measured silicon results were found for any TT bandgap.

## Lessons applied to this design

- MIM unit capacitors work on TT (TT06 silicon).
- Comparator kickback and interference on the DAC top plate showed up in TT06 silicon: shield the top plate, consider a preamp, and use off-chip input decoupling.
- Measure the bandgap and PTAT voltages through the ADC (with an external VREF), not only through the lossy analog mux.
