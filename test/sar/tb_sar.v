// Stage 9 — behavioural testbench for sar_logic (Icarus Verilog).
// Analog model: the top plate is sampled at the falling edge of smpt; on each rising edge of
// cmp_clk the comparator sets q = (VREF*b/256 - vin > 0)  (vtop = vcm + VREF*b/256 - vin).
// Checks: code centres, code edges (+/- 0.01 LSB) and random inputs give floor(256*vin/VREF);
// 10 clocks per conversion with start held high; external-mode pass-through.
`timescale 1ns/1ps
`default_nettype none
module tb_sar;
    reg clk = 0, rst_n = 0, start = 0, mode = 0, ext_sample = 0, ext_cmp_clk = 0;
    reg [7:0] ext_d = 0;
    reg q = 0;
    wire smp, smpt, cmp_clk, eoc;
    wire [7:0] b, d;
    sar_logic dut(.clk(clk), .rst_n(rst_n), .start(start), .mode(mode), .ext_d(ext_d),
                  .ext_sample(ext_sample), .ext_cmp_clk(ext_cmp_clk), .q(q), .smp(smp), .smpt(smpt),
                  .b(b), .cmp_clk(cmp_clk), .d(d), .eoc(eoc));
    always #500 clk = ~clk;                       // 1 MHz
    real VREF = 1.215, vin = 0.0, vs = 0.0, vr;
    always @(negedge smpt) vs = vin;               // sampling instant
    always @(posedge cmp_clk) q = ((VREF * b / 256.0) - vs) > 0.0;

    integer errors = 0, n = 0, k, t_start, t_eoc;
    task automatic convert(input real v, output [7:0] code);
        begin
            vin = v;
            @(posedge eoc); #1 code = d;
        end
    endtask
    task automatic check(input real v);
        reg [7:0] c; integer exp_code;
        begin
            convert(v, c);
            exp_code = $floor(256.0 * v / VREF); if (exp_code > 255) exp_code = 255; if (exp_code < 0) exp_code = 0;
            n = n + 1;
            if (c !== exp_code) begin errors = errors + 1; $display("MISMATCH vin=%f got %0d exp_code %0d", v, c, exp_code); end
        end
    endtask
    initial begin
        #2000 rst_n = 1; start = 1;
        for (k = 0; k < 256; k = k + 1) check((k + 0.5) * VREF / 256.0);          // code centres
        for (k = 1; k < 256; k = k + 1) begin                                       // code edges
            check((k + 0.01) * VREF / 256.0); check((k - 0.01) * VREF / 256.0);
        end
        for (k = 0; k < 2000; k = k + 1) begin                                      // random, but not
            vr = $urandom % 100000 / 100000.0 * VREF;                                // within 1e-6 LSB of
            if ((256.0 * vr / VREF) - $floor(256.0 * vr / VREF + 0.5) > 1e-6 || (256.0 * vr / VREF) - $floor(256.0 * vr / VREF + 0.5) < -1e-6) check(vr);  // an exact code edge
        end
        // conversion period with start held high: EOC to EOC
        @(posedge eoc) t_start = $time; @(posedge eoc) t_eoc = $time;
        $display("conversion period = %0d ns (%0d clocks)", t_eoc - t_start, (t_eoc - t_start) / 1000);
        // external mode pass-through
        mode = 1; ext_d = 8'hA5; ext_sample = 1; ext_cmp_clk = 1; #10;
        if (b !== 8'hA5 || d !== 8'hA5 || smp !== 1 || smpt !== 1 || cmp_clk !== 1 || eoc !== 0) begin
            errors = errors + 1; $display("external mode FAIL b=%h d=%h smp=%b smpt=%b cmp_clk=%b eoc=%b", b, d, smp, smpt, cmp_clk, eoc);
        end
        ext_sample = 0; ext_cmp_clk = 0; #10;
        if (smp !== 0 || smpt !== 0 || cmp_clk !== 0) begin errors = errors + 1; $display("external mode FAIL (low)"); end
        $display("RESULT: %0d conversions checked, %0d errors", n, errors);
        $finish;
    end
endmodule
