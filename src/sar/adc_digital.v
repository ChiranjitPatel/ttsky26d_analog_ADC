// Top-level digital block for tt_um_chiranjitpatel_sar_adc: pin decoding + sar_logic.
// Pin map: docs/specs/top_level.md. Everything digital lives here, so it is synthesized as one block.
//   ui_in[0]  START   (internal mode) / EXT_D0 (external mode)
//   ui_in[1]  VREF_OE (internal)      / EXT_D1
//   ui_in[2]  -                       / EXT_D2
//   ui_in[3]  BG_PD   (internal)      / EXT_D3
//   ui_in[7:4]                          EXT_D[7:4]
//   uio_in[0] MODE, [1] EXT_SAMPLE, [2] EXT_CMP_CLK, [3] REF_SEL, [7:6] INSEL     (inputs)
//   uio_out[4] CMP_OUT, uio_out[5] EOC                                             (outputs)
//   uo_out[7:0] D[7:0]
`default_nettype none
module adc_digital (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] ui_in,
    input  wire [7:0] uio_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    // to / from the analog blocks
    input  wire       q,          // comparator output
    output wire       smp, smpt, cmp_clk,
    output wire [7:0] b,
    output wire       ref_sel,
    output wire       vref_oe,
    output wire       bg_pd,
    output wire [1:0] insel
);
    wire mode = uio_in[0];
    wire eoc;
    sar_logic u_sar (.clk(clk), .rst_n(rst_n), .start(ui_in[0] & ~mode), .mode(mode), .ext_d(ui_in),
                     .ext_sample(uio_in[1]), .ext_cmp_clk(uio_in[2]), .q(q), .smp(smp), .smpt(smpt),
                     .b(b), .cmp_clk(cmp_clk), .d(uo_out), .eoc(eoc));
    assign vref_oe = ui_in[1] & ~mode;
    assign bg_pd   = ui_in[3] & ~mode;
    assign ref_sel = uio_in[3];
    assign insel   = uio_in[7:6];
    assign uio_out = {2'b00, eoc, q, 4'b0000};
    assign uio_oe  = 8'b0011_0000;
endmodule
