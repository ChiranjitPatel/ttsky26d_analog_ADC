// Stage 9 — SAR logic for the 8-bit charge-redistribution ADC (tt_um_chiranjitpatel_sar_adc)
// Switching scheme (sim/inmux/README.md): sample with top plate = vcm and bottom plates = vadc;
// then trial codes on b[7:0]; comparator q = 1 means vtop > vcm, i.e. Vin < trial level -> bit = 0.
//
// Internal mode (mode = 0), 10 clocks per conversion:
//   SAMPLE : smp = 1 (bottom plates track vadc). smpt (falling-edge flip-flop) goes low at the falling
//            edge of clk in this cycle = the sampling instant (bottom-plate sampling); it returns high
//            at the falling edge of the EOC cycle.
//   BIT7..BIT0 : on the rising edge the trial code is applied; the DAC settles while clk is high;
//            the comparator evaluates while clk is low (cmp_clk = ~clk); on the next rising edge the
//            decision is used (keep the bit if q = 0) and the next trial code is applied.
//   EOC    : result loaded into d[7:0], eoc = 1 for this cycle.
//   A conversion starts on a clk rising edge when start = 1 (start is synchronised); if start
//   stays high, conversions repeat back to back (100 kS/s at 1 MHz).
// External mode (mode = 1): b = ext_d, smp = smpt = ext_sample, cmp_clk = ext_cmp_clk,
//   d mirrors ext_d (loopback check), eoc = 0. The comparator output is visible in both modes.
`default_nettype none
module sar_logic (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire       mode,
    input  wire [7:0] ext_d,
    input  wire       ext_sample,
    input  wire       ext_cmp_clk,
    input  wire       q,           // comparator output (SR latch, valid while clk is high)
    output wire       smp,         // bottom plates -> vadc
    output wire       smpt,        // top plate -> vcm
    output wire [7:0] b,           // DAC code
    output wire       cmp_clk,     // comparator clock (evaluate when high)
    output wire [7:0] d,           // conversion result
    output wire       eoc
);
    localparam S_IDLE = 2'd0, S_SAMPLE = 2'd1, S_CONV = 2'd2, S_EOC = 2'd3;
    reg [1:0] state;
    reg [2:0] bitn;        // bit under trial (7 .. 0)
    reg [7:0] code;        // decided bits + trial bit
    reg [7:0] result;
    reg       start_s;     // synchronised start

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; bitn <= 3'd7; code <= 8'd0; result <= 8'd0; start_s <= 1'b0;
        end else begin
            start_s <= start;
            case (state)
                S_IDLE:   if (start_s) state <= S_SAMPLE;
                S_SAMPLE: begin state <= S_CONV; bitn <= 3'd7; code <= 8'b1000_0000; end
                S_CONV: begin
                    // decision for the bit under trial: keep it (1) if the comparator said vtop < vcm
                    if (q) code[bitn] <= 1'b0;
                    if (bitn == 3'd0) begin
                        state  <= S_EOC;
                        result <= {code[7:1], ~q};
                    end else begin
                        code[bitn - 3'd1] <= 1'b1;
                        bitn <= bitn - 3'd1;
                    end
                end
                S_EOC:    state <= start_s ? S_SAMPLE : S_IDLE;
            endcase
        end
    end

    wire tracking = (state == S_IDLE) || (state == S_SAMPLE) || (state == S_EOC);
    // Top-plate switch: a falling-edge flip-flop, so it is glitch-free. It opens at the falling edge of
    // the SAMPLE cycle (the sampling instant), stays open through CONV, and closes again at the falling
    // edge of the EOC cycle. (A combinational version, tracking & ~(SAMPLE & ~clk), glitched high on the
    // rising edge that ends SAMPLE - clk rose before the state left SAMPLE - and re-sampled the top plate
    // while the bottom plates switched. Found in integration stage I2.)
    reg smpt_r;
    always @(negedge clk or negedge rst_n)
        if (!rst_n) smpt_r <= 1'b1;
        else        smpt_r <= ~((state == S_SAMPLE) || (state == S_CONV));
    assign smp     = mode ? ext_sample  : tracking;
    assign smpt    = mode ? ext_sample  : smpt_r;
    assign b       = mode ? ext_d       : (state == S_CONV ? code : 8'd0);
    assign cmp_clk = mode ? ext_cmp_clk : ((state == S_CONV) & ~clk);
    assign d       = mode ? ext_d       : result;
    assign eoc     = mode ? 1'b0        : (state == S_EOC);
endmodule
