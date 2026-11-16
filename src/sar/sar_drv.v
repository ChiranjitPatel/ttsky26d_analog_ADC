// Switch drivers for the analog blocks (M2, 2026-11-16). This gating used to be transistor logic inside
// dac_sw (NOR / NAND per bit) and inmux (2-to-4 decoder); it moved here so the analog cells hold only the
// switches and the logic is placed as dense standard cells with the rest of adc_digital.
//   dac_sw bit i: gn[i]  = NOR(smp, b[i])    -> nfet bp -> VGND   (on when not sampling and b = 0)
//                 gpb[i] = NAND(smpb, b[i])  -> pfet bp -> vref   (on, i.e. low, when not sampling and b = 1)
//                 smp / smpb                 -> sampling TG bp <-> vadc (all bits)
//   termination cap: b tied low -> gn = smpb, gpb = 1 (tied in the analog block)
//   inmux: en[k] / enb[k] for the TG of input k = insel (0 VIN, 1 VPTAT, 2 VBG, 3 VGND), one-hot
//   comparator: cmp_clkb = ~cmp_clk (the StrongARM's tail and reset switches), and the NAND SR latch on
//            its buffered outputs opb / onb: q = NAND(opb, qb), qb = NAND(onb, q); holds while opb = onb = 1.
//            Two explicit nand2 cells, so synthesis keeps the cross-coupled loop as drawn (was transistors in
//            the comparator until 2026-11-16).
`default_nettype none
module sar_drv (
    input  wire       smp,
    input  wire [7:0] b,
    input  wire [1:0] insel,
    input  wire       cmp_clk,
    input  wire       opb, onb,
    output wire       smpb,
    output wire [7:0] gn,
    output wire [7:0] gpb,
    output wire [3:0] en,
    output wire [3:0] enb,
    output wire       cmp_clkb,
    output wire       q
);
    wire qb;
    sky130_fd_sc_hd__nand2_1 u_lq  (.A(opb), .B(qb), .Y(q));
    sky130_fd_sc_hd__nand2_1 u_lqb (.A(onb), .B(q),  .Y(qb));
    assign cmp_clkb = ~cmp_clk;
    assign smpb = ~smp;
    assign gn   = ~({8{smp}} | b);
    assign gpb  = ~({8{smpb}} & b);
    assign en   = 4'b0001 << insel;
    assign enb  = ~en;
endmodule
