module adc_digital (bg_pd,
    clk,
    cmp_clkb,
    cmp_out,
    eoc,
    onb,
    opb,
    ref_sel,
    rst_n,
    smp,
    smpb,
    smpt,
    vref_oe,
    en,
    enb,
    gn,
    gpb,
    ui_in,
    uio_in,
    uo_out);
 output bg_pd;
 input clk;
 output cmp_clkb;
 output cmp_out;
 output eoc;
 input onb;
 input opb;
 output ref_sel;
 input rst_n;
 output smp;
 output smpb;
 output smpt;
 output vref_oe;
 output [3:0] en;
 output [3:0] enb;
 output [7:0] gn;
 output [7:0] gpb;
 input [7:0] ui_in;
 input [7:0] uio_in;
 output [7:0] uo_out;

 wire _000_;
 wire _001_;
 wire _002_;
 wire _003_;
 wire _004_;
 wire clknet_0_clk;
 wire _006_;
 wire _007_;
 wire _008_;
 wire _009_;
 wire _010_;
 wire _011_;
 wire _012_;
 wire _013_;
 wire _014_;
 wire _015_;
 wire _016_;
 wire _017_;
 wire _018_;
 wire _019_;
 wire _020_;
 wire _021_;
 wire _022_;
 wire _023_;
 wire _024_;
 wire _025_;
 wire _026_;
 wire _027_;
 wire _028_;
 wire _029_;
 wire _030_;
 wire _031_;
 wire _032_;
 wire _033_;
 wire _034_;
 wire _035_;
 wire _036_;
 wire _037_;
 wire _038_;
 wire _039_;
 wire _040_;
 wire _041_;
 wire _042_;
 wire _043_;
 wire _044_;
 wire _045_;
 wire _046_;
 wire _047_;
 wire _048_;
 wire _049_;
 wire _050_;
 wire _051_;
 wire _052_;
 wire _053_;
 wire _054_;
 wire _055_;
 wire _056_;
 wire _057_;
 wire _058_;
 wire _059_;
 wire _060_;
 wire _061_;
 wire _062_;
 wire _063_;
 wire _064_;
 wire _065_;
 wire net10;
 wire net8;
 wire net7;
 wire net6;
 wire net5;
 wire net4;
 wire net3;
 wire net2;
 wire net1;
 wire net9;
 wire \u_drv.qb ;
 wire \u_sar.bitn[0] ;
 wire \u_sar.bitn[1] ;
 wire \u_sar.bitn[2] ;
 wire \u_sar.code[0] ;
 wire \u_sar.code[1] ;
 wire \u_sar.code[2] ;
 wire \u_sar.code[3] ;
 wire \u_sar.code[4] ;
 wire \u_sar.code[5] ;
 wire \u_sar.code[6] ;
 wire \u_sar.code[7] ;
 wire \u_sar.result[0] ;
 wire \u_sar.result[1] ;
 wire \u_sar.result[2] ;
 wire \u_sar.result[3] ;
 wire \u_sar.result[4] ;
 wire \u_sar.result[5] ;
 wire \u_sar.result[6] ;
 wire \u_sar.result[7] ;
 wire \u_sar.smpt_r ;
 wire \u_sar.start ;
 wire \u_sar.start_s ;
 wire \u_sar.state[0] ;
 wire \u_sar.state[1] ;
 wire \u_sar.state[2] ;
 wire \u_sar.state[3] ;
 wire net11;
 wire net12;
 wire net13;
 wire net14;
 wire net15;
 wire net16;
 wire net17;
 wire net18;
 wire net19;
 wire clknet_2_0__leaf_clk;
 wire clknet_2_1__leaf_clk;
 wire clknet_2_2__leaf_clk;
 wire clknet_2_3__leaf_clk;
 wire net20;
 wire net21;
 wire net22;
 wire net23;
 wire net24;
 wire net25;
 wire net26;
 wire net27;
 wire net28;
 wire net29;
 wire net30;
 wire net31;
 wire net32;
 wire net33;
 wire net34;
 wire net35;
 wire net36;
 wire net37;
 wire net38;
 wire net39;
 wire net40;
 wire net41;
 wire net42;
 wire net43;
 wire net44;
 wire net45;
 wire net46;
 wire net47;

 sky130_fd_sc_hd__diode_2 ANTENNA_1 (.DIODE(ui_in[5]));
 sky130_fd_sc_hd__fill_1 FILLER_0_113 ();
 sky130_fd_sc_hd__fill_2 FILLER_0_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_8 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_83 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_78 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_126 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_11_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_71 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_126 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_27 ();
 sky130_fd_sc_hd__decap_3 FILLER_12_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_12_82 ();
 sky130_fd_sc_hd__fill_2 FILLER_13_110 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_35 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_85 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_110 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_38 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_66 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_125 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_26 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_37 ();
 sky130_fd_sc_hd__fill_2 FILLER_3_110 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_15 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_18 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_28 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_31 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_50 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_84 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_26 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_50 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_10 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_19 ();
 sky130_fd_sc_hd__fill_2 FILLER_5_37 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_65 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_49 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_126 ();
 sky130_fd_sc_hd__decap_3 FILLER_7_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_30 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_47 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_89 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_111 ();
 sky130_fd_sc_hd__fill_2 FILLER_8_125 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_27 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_29 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_40 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_49 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_52 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_75 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_9_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_44 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_57 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_66 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_97 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Left_15 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Right_0 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Left_25 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Right_10 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Left_26 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Right_11 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Left_27 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Right_12 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Left_28 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Right_13 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_14_Left_29 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_14_Right_14 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Left_16 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Right_1 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Left_17 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Right_2 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Left_18 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Right_3 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Left_19 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Right_4 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Left_20 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Right_5 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Left_21 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Right_6 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Left_22 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Right_7 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Left_23 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Right_8 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Left_24 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Right_9 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_30 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_31 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_32 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_33 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_52 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_53 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_54 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_55 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_56 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_57 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_58 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_59 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_60 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_61 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_62 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_63 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_34 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_35 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_36 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_37 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_38 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_39 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_40 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_41 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_42 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_43 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_44 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_45 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_46 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_47 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_48 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_49 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_50 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_51 ();
 sky130_fd_sc_hd__inv_2 _066_ (.A(\u_sar.state[1] ),
    .Y(_025_));
 sky130_fd_sc_hd__inv_2 _067_ (.A(\u_sar.code[2] ),
    .Y(_026_));
 sky130_fd_sc_hd__inv_2 _068__18 (.A(clknet_2_2__leaf_clk),
    .Y(net18));
 sky130_fd_sc_hd__inv_2 _068__19 (.A(clknet_2_2__leaf_clk),
    .Y(net19));
 sky130_fd_sc_hd__inv_2 _069_ (.A(\u_sar.bitn[0] ),
    .Y(_027_));
 sky130_fd_sc_hd__inv_2 _070_ (.A(\u_sar.bitn[2] ),
    .Y(_028_));
 sky130_fd_sc_hd__inv_2 _071_ (.A(net10),
    .Y(_029_));
 sky130_fd_sc_hd__and2b_2 _072_ (.A_N(net14),
    .B(\u_sar.state[3] ),
    .X(eoc));
 sky130_fd_sc_hd__mux2_1 _073_ (.A0(\u_sar.result[0] ),
    .A1(ui_in[0]),
    .S(net12),
    .X(uo_out[0]));
 sky130_fd_sc_hd__mux2_1 _074_ (.A0(\u_sar.result[1] ),
    .A1(ui_in[1]),
    .S(net12),
    .X(uo_out[1]));
 sky130_fd_sc_hd__mux2_1 _075_ (.A0(\u_sar.result[2] ),
    .A1(ui_in[2]),
    .S(net12),
    .X(uo_out[2]));
 sky130_fd_sc_hd__mux2_1 _076_ (.A0(\u_sar.result[3] ),
    .A1(ui_in[3]),
    .S(net14),
    .X(uo_out[3]));
 sky130_fd_sc_hd__mux2_1 _077_ (.A0(\u_sar.result[4] ),
    .A1(ui_in[4]),
    .S(net14),
    .X(uo_out[4]));
 sky130_fd_sc_hd__mux2_1 _078_ (.A0(\u_sar.result[5] ),
    .A1(ui_in[5]),
    .S(net14),
    .X(uo_out[5]));
 sky130_fd_sc_hd__mux2_1 _079_ (.A0(\u_sar.result[6] ),
    .A1(ui_in[6]),
    .S(net14),
    .X(uo_out[6]));
 sky130_fd_sc_hd__mux2_1 _080_ (.A0(\u_sar.result[7] ),
    .A1(ui_in[7]),
    .S(net12),
    .X(uo_out[7]));
 sky130_fd_sc_hd__nand2b_2 _081_ (.A_N(uio_in[1]),
    .B(net12),
    .Y(_030_));
 sky130_fd_sc_hd__o21a_2 _082_ (.A1(net12),
    .A2(\u_sar.smpt_r ),
    .B1(_030_),
    .X(smpt));
 sky130_fd_sc_hd__nor2_2 _083_ (.A(\u_sar.state[2] ),
    .B(\u_sar.state[1] ),
    .Y(_004_));
 sky130_fd_sc_hd__or2_2 _084_ (.A(uio_in[7]),
    .B(uio_in[6]),
    .X(enb[0]));
 sky130_fd_sc_hd__inv_2 _085_ (.A(enb[0]),
    .Y(en[0]));
 sky130_fd_sc_hd__nand2b_2 _086_ (.A_N(uio_in[7]),
    .B(uio_in[6]),
    .Y(enb[1]));
 sky130_fd_sc_hd__inv_2 _087_ (.A(enb[1]),
    .Y(en[1]));
 sky130_fd_sc_hd__nand2b_2 _088_ (.A_N(uio_in[6]),
    .B(uio_in[7]),
    .Y(enb[2]));
 sky130_fd_sc_hd__inv_2 _089_ (.A(enb[2]),
    .Y(en[2]));
 sky130_fd_sc_hd__nand2_2 _090_ (.A(uio_in[7]),
    .B(uio_in[6]),
    .Y(enb[3]));
 sky130_fd_sc_hd__inv_2 _091_ (.A(enb[3]),
    .Y(en[3]));
 sky130_fd_sc_hd__nor2_2 _092_ (.A(\u_sar.state[3] ),
    .B(\u_sar.state[0] ),
    .Y(_031_));
 sky130_fd_sc_hd__or2_2 _093_ (.A(\u_sar.state[3] ),
    .B(\u_sar.state[0] ),
    .X(_032_));
 sky130_fd_sc_hd__o31a_2 _094_ (.A1(net12),
    .A2(\u_sar.state[2] ),
    .A3(_032_),
    .B1(_030_),
    .X(net9));
 sky130_fd_sc_hd__inv_2 _095_ (.A(smp),
    .Y(smpb));
 sky130_fd_sc_hd__and2b_2 _096_ (.A_N(net12),
    .B(\u_sar.state[1] ),
    .X(_033_));
 sky130_fd_sc_hd__a22o_2 _097_ (.A1(net12),
    .A2(ui_in[0]),
    .B1(\u_sar.code[0] ),
    .B2(_033_),
    .X(_034_));
 sky130_fd_sc_hd__nand2_2 _098_ (.A(smpb),
    .B(_034_),
    .Y(gpb[0]));
 sky130_fd_sc_hd__a22o_2 _099_ (.A1(net13),
    .A2(ui_in[1]),
    .B1(\u_sar.code[1] ),
    .B2(_033_),
    .X(_035_));
 sky130_fd_sc_hd__nand2_2 _100_ (.A(smpb),
    .B(_035_),
    .Y(gpb[1]));
 sky130_fd_sc_hd__a22o_2 _101_ (.A1(net13),
    .A2(ui_in[2]),
    .B1(\u_sar.code[2] ),
    .B2(_033_),
    .X(_036_));
 sky130_fd_sc_hd__nand2_2 _102_ (.A(smpb),
    .B(_036_),
    .Y(gpb[2]));
 sky130_fd_sc_hd__a22o_2 _103_ (.A1(net13),
    .A2(ui_in[3]),
    .B1(\u_sar.code[3] ),
    .B2(_033_),
    .X(_037_));
 sky130_fd_sc_hd__nand2_2 _104_ (.A(smpb),
    .B(_037_),
    .Y(gpb[3]));
 sky130_fd_sc_hd__a22o_2 _105_ (.A1(net14),
    .A2(ui_in[4]),
    .B1(\u_sar.code[4] ),
    .B2(_033_),
    .X(_038_));
 sky130_fd_sc_hd__nand2_2 _106_ (.A(smpb),
    .B(_038_),
    .Y(gpb[4]));
 sky130_fd_sc_hd__a22o_2 _107_ (.A1(net14),
    .A2(ui_in[5]),
    .B1(\u_sar.code[5] ),
    .B2(_033_),
    .X(_039_));
 sky130_fd_sc_hd__nand2_2 _108_ (.A(smpb),
    .B(_039_),
    .Y(gpb[5]));
 sky130_fd_sc_hd__a22o_2 _109_ (.A1(net14),
    .A2(ui_in[6]),
    .B1(\u_sar.code[6] ),
    .B2(_033_),
    .X(_040_));
 sky130_fd_sc_hd__nand2_2 _110_ (.A(smpb),
    .B(_040_),
    .Y(gpb[6]));
 sky130_fd_sc_hd__a22o_2 _111_ (.A1(net13),
    .A2(ui_in[7]),
    .B1(\u_sar.code[7] ),
    .B2(_033_),
    .X(_041_));
 sky130_fd_sc_hd__nand2_2 _112_ (.A(smpb),
    .B(_041_),
    .Y(gpb[7]));
 sky130_fd_sc_hd__nor2_2 _113_ (.A(smp),
    .B(_034_),
    .Y(net8));
 sky130_fd_sc_hd__nor2_2 _114_ (.A(smp),
    .B(_035_),
    .Y(net7));
 sky130_fd_sc_hd__nor2_2 _115_ (.A(smp),
    .B(_036_),
    .Y(net6));
 sky130_fd_sc_hd__nor2_2 _116_ (.A(smp),
    .B(_037_),
    .Y(net5));
 sky130_fd_sc_hd__nor2_2 _117_ (.A(net9),
    .B(_038_),
    .Y(net4));
 sky130_fd_sc_hd__nor2_2 _118_ (.A(net9),
    .B(_039_),
    .Y(net3));
 sky130_fd_sc_hd__nor2_2 _119_ (.A(net9),
    .B(_040_),
    .Y(net2));
 sky130_fd_sc_hd__nor2_2 _120_ (.A(net9),
    .B(_041_),
    .Y(net1));
 sky130_fd_sc_hd__a22oi_2 _121_ (.A1(net12),
    .A2(uio_in[2]),
    .B1(net19),
    .B2(_033_),
    .Y(cmp_clkb));
 sky130_fd_sc_hd__nor2_2 _122_ (.A(net11),
    .B(\u_sar.bitn[0] ),
    .Y(_042_));
 sky130_fd_sc_hd__or3_2 _123_ (.A(net11),
    .B(\u_sar.bitn[0] ),
    .C(\u_sar.bitn[2] ),
    .X(_043_));
 sky130_fd_sc_hd__or4b_2 _124_ (.A(net11),
    .B(\u_sar.bitn[0] ),
    .C(\u_sar.bitn[2] ),
    .D_N(\u_sar.state[1] ),
    .X(_044_));
 sky130_fd_sc_hd__inv_2 _125_ (.A(_044_),
    .Y(_002_));
 sky130_fd_sc_hd__and2_2 _126_ (.A(net20),
    .B(_032_),
    .X(_001_));
 sky130_fd_sc_hd__nor2_2 _127_ (.A(net20),
    .B(_031_),
    .Y(_000_));
 sky130_fd_sc_hd__and2b_2 _128_ (.A_N(net13),
    .B(ui_in[0]),
    .X(\u_sar.start ));
 sky130_fd_sc_hd__and2b_2 _129_ (.A_N(net14),
    .B(ui_in[1]),
    .X(vref_oe));
 sky130_fd_sc_hd__and2b_2 _130_ (.A_N(net14),
    .B(ui_in[3]),
    .X(bg_pd));
 sky130_fd_sc_hd__a21o_2 _131_ (.A1(\u_sar.state[1] ),
    .A2(_043_),
    .B1(net37),
    .X(_003_));
 sky130_fd_sc_hd__and2b_2 _132_ (.A_N(_004_),
    .B(_044_),
    .X(_045_));
 sky130_fd_sc_hd__mux2_1 _133_ (.A0(_025_),
    .A1(_045_),
    .S(_027_),
    .X(_006_));
 sky130_fd_sc_hd__and2_2 _134_ (.A(net11),
    .B(\u_sar.bitn[0] ),
    .X(_046_));
 sky130_fd_sc_hd__nand2_2 _135_ (.A(net11),
    .B(\u_sar.bitn[0] ),
    .Y(_047_));
 sky130_fd_sc_hd__and2b_2 _136_ (.A_N(\u_sar.bitn[0] ),
    .B(net11),
    .X(_048_));
 sky130_fd_sc_hd__o32a_2 _137_ (.A1(_025_),
    .A2(_042_),
    .A3(_046_),
    .B1(_045_),
    .B2(net44),
    .X(_007_));
 sky130_fd_sc_hd__a21oi_2 _138_ (.A1(net37),
    .A2(_025_),
    .B1(\u_sar.bitn[2] ),
    .Y(_049_));
 sky130_fd_sc_hd__a21oi_2 _139_ (.A1(net39),
    .A2(_042_),
    .B1(_049_),
    .Y(_008_));
 sky130_fd_sc_hd__nor2_2 _140_ (.A(\u_sar.state[1] ),
    .B(_032_),
    .Y(_050_));
 sky130_fd_sc_hd__nand2_2 _141_ (.A(_025_),
    .B(_031_),
    .Y(_051_));
 sky130_fd_sc_hd__or3b_2 _142_ (.A(\u_sar.state[3] ),
    .B(\u_sar.state[0] ),
    .C_N(net10),
    .X(_052_));
 sky130_fd_sc_hd__o21ai_2 _143_ (.A1(_043_),
    .A2(_052_),
    .B1(net43),
    .Y(_053_));
 sky130_fd_sc_hd__or4_2 _144_ (.A(\u_sar.bitn[1] ),
    .B(_027_),
    .C(\u_sar.bitn[2] ),
    .D(_032_),
    .X(_054_));
 sky130_fd_sc_hd__a21oi_2 _145_ (.A1(_053_),
    .A2(_054_),
    .B1(_050_),
    .Y(_009_));
 sky130_fd_sc_hd__and4_2 _146_ (.A(\u_sar.state[1] ),
    .B(_028_),
    .C(_031_),
    .D(_048_),
    .X(_055_));
 sky130_fd_sc_hd__or4_2 _147_ (.A(\u_sar.bitn[1] ),
    .B(_027_),
    .C(\u_sar.bitn[2] ),
    .D(_052_),
    .X(_056_));
 sky130_fd_sc_hd__a31o_2 _148_ (.A1(net38),
    .A2(_051_),
    .A3(_056_),
    .B1(_055_),
    .X(_010_));
 sky130_fd_sc_hd__a41o_2 _149_ (.A1(_028_),
    .A2(net10),
    .A3(_031_),
    .A4(_048_),
    .B1(_026_),
    .X(_057_));
 sky130_fd_sc_hd__or3_2 _150_ (.A(\u_sar.bitn[2] ),
    .B(_032_),
    .C(_047_),
    .X(_058_));
 sky130_fd_sc_hd__a21oi_2 _151_ (.A1(_057_),
    .A2(_058_),
    .B1(_050_),
    .Y(_011_));
 sky130_fd_sc_hd__and3_2 _152_ (.A(\u_sar.state[1] ),
    .B(\u_sar.bitn[2] ),
    .C(_031_),
    .X(_059_));
 sky130_fd_sc_hd__or3_2 _153_ (.A(\u_sar.bitn[2] ),
    .B(_047_),
    .C(_052_),
    .X(_060_));
 sky130_fd_sc_hd__a32o_2 _154_ (.A1(net45),
    .A2(_051_),
    .A3(_060_),
    .B1(_059_),
    .B2(_042_),
    .X(_012_));
 sky130_fd_sc_hd__and4b_2 _155_ (.A_N(net11),
    .B(\u_sar.bitn[0] ),
    .C(\u_sar.bitn[2] ),
    .D(_031_),
    .X(_061_));
 sky130_fd_sc_hd__o31a_2 _156_ (.A1(net11),
    .A2(_028_),
    .A3(_052_),
    .B1(net47),
    .X(_062_));
 sky130_fd_sc_hd__o21a_2 _157_ (.A1(_061_),
    .A2(_062_),
    .B1(_051_),
    .X(_013_));
 sky130_fd_sc_hd__or4_2 _158_ (.A(net11),
    .B(_027_),
    .C(_028_),
    .D(_052_),
    .X(_063_));
 sky130_fd_sc_hd__a32o_2 _159_ (.A1(net41),
    .A2(_051_),
    .A3(_063_),
    .B1(_059_),
    .B2(_048_),
    .X(_014_));
 sky130_fd_sc_hd__or4b_2 _160_ (.A(\u_sar.bitn[0] ),
    .B(_028_),
    .C(_052_),
    .D_N(net11),
    .X(_064_));
 sky130_fd_sc_hd__a32o_2 _161_ (.A1(net42),
    .A2(_051_),
    .A3(_064_),
    .B1(_059_),
    .B2(_046_),
    .X(_015_));
 sky130_fd_sc_hd__o31a_2 _162_ (.A1(_028_),
    .A2(_047_),
    .A3(_052_),
    .B1(net46),
    .X(_065_));
 sky130_fd_sc_hd__or2_2 _163_ (.A(_050_),
    .B(_065_),
    .X(_016_));
 sky130_fd_sc_hd__mux2_1 _164_ (.A0(_029_),
    .A1(net30),
    .S(_044_),
    .X(_017_));
 sky130_fd_sc_hd__mux2_1 _165_ (.A0(\u_sar.code[1] ),
    .A1(net31),
    .S(_044_),
    .X(_018_));
 sky130_fd_sc_hd__mux2_1 _166_ (.A0(\u_sar.code[2] ),
    .A1(net33),
    .S(_044_),
    .X(_019_));
 sky130_fd_sc_hd__mux2_1 _167_ (.A0(\u_sar.code[3] ),
    .A1(net28),
    .S(_044_),
    .X(_020_));
 sky130_fd_sc_hd__mux2_1 _168_ (.A0(\u_sar.code[4] ),
    .A1(net24),
    .S(_044_),
    .X(_021_));
 sky130_fd_sc_hd__mux2_1 _169_ (.A0(\u_sar.code[5] ),
    .A1(net35),
    .S(_044_),
    .X(_022_));
 sky130_fd_sc_hd__mux2_1 _170_ (.A0(\u_sar.code[6] ),
    .A1(net22),
    .S(_044_),
    .X(_023_));
 sky130_fd_sc_hd__mux2_1 _171_ (.A0(\u_sar.code[7] ),
    .A1(net26),
    .S(_044_),
    .X(_024_));
 sky130_fd_sc_hd__dfstp_2 _172_ (.CLK(clknet_2_2__leaf_clk),
    .D(_006_),
    .SET_B(net16),
    .Q(\u_sar.bitn[0] ));
 sky130_fd_sc_hd__dfstp_2 _173_ (.CLK(clknet_2_0__leaf_clk),
    .D(_007_),
    .SET_B(net15),
    .Q(\u_sar.bitn[1] ));
 sky130_fd_sc_hd__dfstp_2 _174_ (.CLK(clknet_2_2__leaf_clk),
    .D(net40),
    .SET_B(net16),
    .Q(\u_sar.bitn[2] ));
 sky130_fd_sc_hd__dfrtp_2 _175_ (.CLK(clknet_2_2__leaf_clk),
    .D(_009_),
    .RESET_B(net16),
    .Q(\u_sar.code[0] ));
 sky130_fd_sc_hd__dfrtp_2 _176_ (.CLK(clknet_2_1__leaf_clk),
    .D(_010_),
    .RESET_B(net16),
    .Q(\u_sar.code[1] ));
 sky130_fd_sc_hd__dfrtp_2 _177_ (.CLK(clknet_2_3__leaf_clk),
    .D(_011_),
    .RESET_B(net16),
    .Q(\u_sar.code[2] ));
 sky130_fd_sc_hd__dfrtp_2 _178_ (.CLK(clknet_2_0__leaf_clk),
    .D(_012_),
    .RESET_B(net15),
    .Q(\u_sar.code[3] ));
 sky130_fd_sc_hd__dfrtp_2 _179_ (.CLK(clknet_2_0__leaf_clk),
    .D(_013_),
    .RESET_B(net15),
    .Q(\u_sar.code[4] ));
 sky130_fd_sc_hd__dfrtp_2 _180_ (.CLK(clknet_2_0__leaf_clk),
    .D(_014_),
    .RESET_B(net15),
    .Q(\u_sar.code[5] ));
 sky130_fd_sc_hd__dfrtp_2 _181_ (.CLK(clknet_2_0__leaf_clk),
    .D(_015_),
    .RESET_B(net15),
    .Q(\u_sar.code[6] ));
 sky130_fd_sc_hd__dfrtp_2 _182_ (.CLK(clknet_2_0__leaf_clk),
    .D(_016_),
    .RESET_B(net15),
    .Q(\u_sar.code[7] ));
 sky130_fd_sc_hd__dfrtp_2 _183_ (.CLK(clknet_2_3__leaf_clk),
    .D(_017_),
    .RESET_B(net16),
    .Q(\u_sar.result[0] ));
 sky130_fd_sc_hd__dfrtp_2 _184_ (.CLK(clknet_2_1__leaf_clk),
    .D(net32),
    .RESET_B(net15),
    .Q(\u_sar.result[1] ));
 sky130_fd_sc_hd__dfrtp_2 _185_ (.CLK(clknet_2_3__leaf_clk),
    .D(net34),
    .RESET_B(net16),
    .Q(\u_sar.result[2] ));
 sky130_fd_sc_hd__dfrtp_2 _186_ (.CLK(clknet_2_1__leaf_clk),
    .D(net29),
    .RESET_B(net15),
    .Q(\u_sar.result[3] ));
 sky130_fd_sc_hd__dfrtp_2 _187_ (.CLK(clknet_2_1__leaf_clk),
    .D(net25),
    .RESET_B(net15),
    .Q(\u_sar.result[4] ));
 sky130_fd_sc_hd__dfrtp_2 _188_ (.CLK(clknet_2_0__leaf_clk),
    .D(net36),
    .RESET_B(net15),
    .Q(\u_sar.result[5] ));
 sky130_fd_sc_hd__dfrtp_2 _189_ (.CLK(clknet_2_1__leaf_clk),
    .D(net23),
    .RESET_B(net17),
    .Q(\u_sar.result[6] ));
 sky130_fd_sc_hd__dfrtp_2 _190_ (.CLK(clknet_2_1__leaf_clk),
    .D(net27),
    .RESET_B(net17),
    .Q(\u_sar.result[7] ));
 sky130_fd_sc_hd__dfstp_2 _191_ (.CLK(clknet_2_3__leaf_clk),
    .D(net21),
    .SET_B(net17),
    .Q(\u_sar.state[0] ));
 sky130_fd_sc_hd__dfrtp_2 _192_ (.CLK(clknet_2_2__leaf_clk),
    .D(_003_),
    .RESET_B(net16),
    .Q(\u_sar.state[1] ));
 sky130_fd_sc_hd__dfrtp_2 _193_ (.CLK(clknet_2_2__leaf_clk),
    .D(_001_),
    .RESET_B(net16),
    .Q(\u_sar.state[2] ));
 sky130_fd_sc_hd__dfrtp_2 _194_ (.CLK(clknet_2_3__leaf_clk),
    .D(_002_),
    .RESET_B(net17),
    .Q(\u_sar.state[3] ));
 sky130_fd_sc_hd__dfrtp_2 _195_ (.CLK(clknet_2_3__leaf_clk),
    .D(\u_sar.start ),
    .RESET_B(net17),
    .Q(\u_sar.start_s ));
 sky130_fd_sc_hd__dfstp_2 _196_ (.CLK(net18),
    .D(_004_),
    .SET_B(net16),
    .Q(\u_sar.smpt_r ));
 sky130_fd_sc_hd__buf_2 _197_ (.A(uio_in[3]),
    .X(ref_sel));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_0_clk (.A(clk),
    .X(clknet_0_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_2_0__f_clk (.A(clknet_0_clk),
    .X(clknet_2_0__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_2_1__f_clk (.A(clknet_0_clk),
    .X(clknet_2_1__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_2_2__f_clk (.A(clknet_0_clk),
    .X(clknet_2_2__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_2_3__f_clk (.A(clknet_0_clk),
    .X(clknet_2_3__leaf_clk));
 sky130_fd_sc_hd__clkinv_2 clkload0 (.A(clknet_2_0__leaf_clk));
 sky130_fd_sc_hd__bufinv_16 clkload1 (.A(clknet_2_1__leaf_clk));
 sky130_fd_sc_hd__bufinv_16 clkload2 (.A(clknet_2_3__leaf_clk));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout11 (.A(\u_sar.bitn[1] ),
    .X(net11));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout12 (.A(uio_in[0]),
    .X(net12));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout13 (.A(uio_in[0]),
    .X(net13));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout14 (.A(uio_in[0]),
    .X(net14));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout15 (.A(net17),
    .X(net15));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout16 (.A(net17),
    .X(net16));
 sky130_fd_sc_hd__clkdlybuf4s25_1 fanout17 (.A(rst_n),
    .X(net17));
 sky130_fd_sc_hd__dlygate4sd3_1 hold20 (.A(\u_sar.start_s ),
    .X(net20));
 sky130_fd_sc_hd__dlygate4sd3_1 hold21 (.A(_000_),
    .X(net21));
 sky130_fd_sc_hd__dlygate4sd3_1 hold22 (.A(\u_sar.result[6] ),
    .X(net22));
 sky130_fd_sc_hd__dlygate4sd3_1 hold23 (.A(_023_),
    .X(net23));
 sky130_fd_sc_hd__dlygate4sd3_1 hold24 (.A(\u_sar.result[4] ),
    .X(net24));
 sky130_fd_sc_hd__dlygate4sd3_1 hold25 (.A(_021_),
    .X(net25));
 sky130_fd_sc_hd__dlygate4sd3_1 hold26 (.A(\u_sar.result[7] ),
    .X(net26));
 sky130_fd_sc_hd__dlygate4sd3_1 hold27 (.A(_024_),
    .X(net27));
 sky130_fd_sc_hd__dlygate4sd3_1 hold28 (.A(\u_sar.result[3] ),
    .X(net28));
 sky130_fd_sc_hd__dlygate4sd3_1 hold29 (.A(_020_),
    .X(net29));
 sky130_fd_sc_hd__dlygate4sd3_1 hold30 (.A(\u_sar.result[0] ),
    .X(net30));
 sky130_fd_sc_hd__dlygate4sd3_1 hold31 (.A(\u_sar.result[1] ),
    .X(net31));
 sky130_fd_sc_hd__dlygate4sd3_1 hold32 (.A(_018_),
    .X(net32));
 sky130_fd_sc_hd__dlygate4sd3_1 hold33 (.A(\u_sar.result[2] ),
    .X(net33));
 sky130_fd_sc_hd__dlygate4sd3_1 hold34 (.A(_019_),
    .X(net34));
 sky130_fd_sc_hd__dlygate4sd3_1 hold35 (.A(\u_sar.result[5] ),
    .X(net35));
 sky130_fd_sc_hd__dlygate4sd3_1 hold36 (.A(_022_),
    .X(net36));
 sky130_fd_sc_hd__dlygate4sd3_1 hold37 (.A(\u_sar.state[2] ),
    .X(net37));
 sky130_fd_sc_hd__dlygate4sd3_1 hold38 (.A(\u_sar.code[1] ),
    .X(net38));
 sky130_fd_sc_hd__dlygate4sd3_1 hold39 (.A(\u_sar.state[1] ),
    .X(net39));
 sky130_fd_sc_hd__dlygate4sd3_1 hold40 (.A(_008_),
    .X(net40));
 sky130_fd_sc_hd__dlygate4sd3_1 hold41 (.A(\u_sar.code[5] ),
    .X(net41));
 sky130_fd_sc_hd__dlygate4sd3_1 hold42 (.A(\u_sar.code[6] ),
    .X(net42));
 sky130_fd_sc_hd__dlygate4sd3_1 hold43 (.A(\u_sar.code[0] ),
    .X(net43));
 sky130_fd_sc_hd__dlygate4sd3_1 hold44 (.A(\u_sar.bitn[1] ),
    .X(net44));
 sky130_fd_sc_hd__dlygate4sd3_1 hold45 (.A(\u_sar.code[3] ),
    .X(net45));
 sky130_fd_sc_hd__dlygate4sd3_1 hold46 (.A(\u_sar.code[7] ),
    .X(net46));
 sky130_fd_sc_hd__dlygate4sd3_1 hold47 (.A(\u_sar.code[4] ),
    .X(net47));
 sky130_fd_sc_hd__buf_6 max_cap9 (.A(net9),
    .X(smp));
 sky130_fd_sc_hd__nand2_1 \u_drv.u_lq  (.A(opb),
    .B(\u_drv.qb ),
    .Y(net10));
 sky130_fd_sc_hd__nand2_1 \u_drv.u_lqb  (.A(onb),
    .B(net10),
    .Y(\u_drv.qb ));
 sky130_fd_sc_hd__clkbuf_4 wire1 (.A(net1),
    .X(gn[7]));
 sky130_fd_sc_hd__clkbuf_4 wire10 (.A(net10),
    .X(cmp_out));
 sky130_fd_sc_hd__clkbuf_4 wire2 (.A(net2),
    .X(gn[6]));
 sky130_fd_sc_hd__clkbuf_4 wire3 (.A(net3),
    .X(gn[5]));
 sky130_fd_sc_hd__clkbuf_4 wire4 (.A(net4),
    .X(gn[4]));
 sky130_fd_sc_hd__clkbuf_4 wire5 (.A(net5),
    .X(gn[3]));
 sky130_fd_sc_hd__clkbuf_4 wire6 (.A(net6),
    .X(gn[2]));
 sky130_fd_sc_hd__clkbuf_4 wire7 (.A(net7),
    .X(gn[1]));
 sky130_fd_sc_hd__clkbuf_4 wire8 (.A(net8),
    .X(gn[0]));
endmodule
