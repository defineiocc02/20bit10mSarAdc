// ============================================================
// [CODE-INDEX] DigitalTop.sv —— 10 MS/s 部分交织数字顶层（单转换链）
// 端口与 analog/netlist/digital_stubs.scs 的 DigitalTop_stub 逐字一致（27 个）。
// 口径：spec/SSOT.md #27–#28；D1=10 bit，D2=12 bit，D1_MASK=18×7=126 bit。
// 时序：CLK200=5 ns/tick；cnt 0..19 一帧(100 ns)；
//       ΦC0 0-1 / ΦC1 2-4 / ΦRA 5-8 / ΦC2 9-17 / guard 18-19。
// 数据流：D1/D2/DT → Sinc2 → ReconWeights → FramePack → DOUT/DRDY。
// Mapper：D1 → 8 lane 码（k 个满量程 + 1 个二进制），按 SLICE_ID 散射到 18 片；
//         bin_lane 由 dem_state 旋转（8 态片级 DEM）。
// ============================================================
`timescale 1ns/1ps

module DigitalTop (
    input  logic        CLK200,
    input  logic        RSTN,

    input  logic [9:0]  D1,
    input  logic [11:0] D2,
    input  logic [7:0]  DT,
    input  logic        DONE1,
    input  logic        DONE2,
    input  logic [14:0] COARSE,

    output logic [17:0] ACQ,
    output logic [17:0] CONV,
    output logic [17:0] EN,
    output logic [17:0] SEL,
    output logic [17:0] SELB,
    output logic [125:0] D1_MASK,

    output logic        PHI_C0,
    output logic        PHI_C1,
    output logic        PHI_RA,
    output logic        PHI_AZ,
    output logic        PHI_C2,
    output logic        PRE,
    output logic        HOLD,
    output logic        EN_RA,

    output logic [21:0] DOUT,
    output logic        DOUT_RDY,
    output logic [7:0]  MON,

    input  logic        VDD18,
    input  logic        GND
);

    logic [4:0] cnt;
    logic       swap;
    logic [4:0] base;
    logic [3:0] m_act;
    logic [2:0] dem_state;

    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) cnt <= 5'd0;
        else       cnt <= (cnt == 5'd19) ? 5'd0 : cnt + 5'd1;
    end

    assign swap = (cnt == 5'd19);

    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) dem_state <= 3'd0;
        else if (swap) dem_state <= dem_state + 3'd1;
    end

    assign PHI_C0 = (cnt <= 5'd1);
    assign PHI_C1 = (cnt >= 5'd2) && (cnt <= 5'd4);
    assign PHI_RA = (cnt >= 5'd5) && (cnt <= 5'd8);
    assign PHI_C2 = (cnt >= 5'd9) && (cnt <= 5'd17);
    assign PHI_AZ = (cnt >= 5'd4) && (cnt <= 5'd6);
    assign PRE    = (cnt <= 5'd1);
    assign HOLD   = (cnt >= 5'd18) || (cnt <= 5'd0);
    assign EN_RA  = PHI_RA;

    SliceSched u_sched (
        .clk(CLK200), .rstn(RSTN), .swap(swap),
        .acq(ACQ), .conv(CONV), .en(EN), .sel(SEL), .selb(SELB),
        .base(base), .m_act(m_act)
    );

    // D1 -> 8 lane 码 -> 18 片物理掩码
    always_comb begin
        int u;
        u = 0;
        D1_MASK = '0;
        for (int j = 0; j < 8; j++) begin
            int idx;
            idx = (base + j) % 18;
            if (j == dem_state) begin
                D1_MASK[7*idx +: 7] = D1[6:0];   // 二进制片
            end else if (u < D1[9:7]) begin
                D1_MASK[7*idx +: 7] = 7'h7F;     // 满量程片
                u = u + 1;
            end
        end
    end

    logic [25:0] acc;
    logic        acc_valid;
    Sinc2 u_sinc (
        .clk(CLK200), .rstn(RSTN),
        .d1(D1), .d2(D2), .dt(DT), .valid(DONE2),
        .acc(acc), .acc_valid(acc_valid)
    );

    logic [21:0] recon;
    ReconWeights u_recon (
        .clk(CLK200), .rstn(RSTN),
        .d1(D1), .d2(D2), .valid(acc_valid), .dout(recon)
    );

    logic [23:0] frame;
    logic        frame_valid, fifo_full;
    FramePack u_fifo (
        .clk(CLK200), .rstn(RSTN),
        .din(recon), .valid_in(acc_valid), .fault(1'b0),
        .dout(frame), .valid_out(frame_valid), .full(fifo_full)
    );

    assign DOUT = frame[21:0];
    assign DOUT_RDY = frame_valid;
    assign MON = {m_act, base[3:0]};

endmodule
