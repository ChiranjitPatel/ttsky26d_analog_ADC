// Checks adc_digital pin decoding: internal-mode gating of START/VREF_OE/BG_PD, uio_oe, uio_out,
// pass-through of REF_SEL/INSEL, and that conversions still run through the wrapper.
`timescale 1ns/1ps
`default_nettype none
module tb_adc_digital;
    reg clk = 0, rst_n = 0; reg [7:0] ui = 0, uio = 0; reg q = 0;
    wire [7:0] uo, uio_out, uio_oe, b; wire smp, smpt, cmp_clk, ref_sel, vref_oe, bg_pd; wire [1:0] insel;
    adc_digital dut(.clk(clk), .rst_n(rst_n), .ui_in(ui), .uio_in(uio), .uo_out(uo), .uio_out(uio_out), .uio_oe(uio_oe),
                    .q(q), .smp(smp), .smpt(smpt), .cmp_clk(cmp_clk), .b(b), .ref_sel(ref_sel), .vref_oe(vref_oe),
                    .bg_pd(bg_pd), .insel(insel));
    always #500 clk = ~clk;
    real VREF = 1.215, vin = 0.5, vs = 0;
    always @(negedge smpt) vs = vin;
    always @(posedge cmp_clk) q = ((VREF * b / 256.0) - vs) > 0.0;
    integer errors = 0;
    task chk(input cond, input [8*40:1] msg); if (!cond) begin errors = errors + 1; $display("FAIL: %0s", msg); end endtask
    initial begin
        #2000 rst_n = 1;
        chk(uio_oe === 8'b0011_0000, "uio_oe");
        ui = 8'b0000_1010; uio = 8'b1100_1000; #10;          // internal: vref_oe, bg_pd set; ref_sel, insel=11
        chk(vref_oe === 1 && bg_pd === 1 && ref_sel === 1 && insel === 2'b11, "internal decode");
        uio = 8'b0000_0001; #10;                              // external mode gates the internal controls
        chk(vref_oe === 0 && bg_pd === 0, "external gating");
        chk(b === 8'b0000_1010 && uo === 8'b0000_1010, "external pass-through");
        uio = 0; ui = 8'b0000_0001; vin = 0.5;                // internal conversion via the wrapper
        @(posedge uio_out[5]); #1;
        chk(uo === 8'd105, "conversion of 0.5 V (expect 105)");
        chk(uio_out[3:0] === 0 && uio_out[7:6] === 0, "unused uio_out low");
        $display("RESULT: %0d errors (code %0d)", errors, uo);
        $finish;
    end
endmodule
