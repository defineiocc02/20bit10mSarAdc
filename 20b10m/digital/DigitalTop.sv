// ============================================================
// [CODE-INDEX] DigitalTop.sv —— 10 MS/s 部分交织数字顶层（单转换链）
// 端口与 analog/netlist/digital_stubs.scs 的 DigitalTop_stub 逐字一致（26 个）。
// 时序：CLK200=5 ns/tick；cnt 0..19 一帧(100 ns)；
//       ΦC0 0-1 / ΦC1 2-4 / ΦRA 5-9 / ΦC2 10-17 / cnt19 swap。
// 数据流：D1/D2/DT → Sinc2 → ReconWeights → FramePack → DOUT/DRDY。
// 注意：本文件是行为级骨架；Sar1Ctrl/Sar2Ctrl 在模拟块的数字壳内，
//       不在本文件例化（见 digital/README.md 的模块表）。
// ============================================================
// DigitalTop.sv —— 10 MS/s 部分交织数字顶层（单转换链）
// 端口与 analog/netlist/digital_stubs.scs 的 DigitalTop_stub 逐字一致。
// 时序：CLK200 = 5 ns tick；帧 20 tick (100 ns)；转换 18 tick (90 ns)。
`timescale 1ns/1ps

module DigitalTop (
    input  logic        CLK200,
    input  logic        RSTN,

    input  logic [10:0] D1,
    input  logic [10:0] D2,
    input  logic [7:0]  DT,
    input  logic        DONE1,
    input  logic        DONE2,
    input  logic [14:0] COARSE,

    output logic [17:0] ACQ,
    output logic [17:0] CONV,
    output logic [17:0] EN,
    output logic [17:0] SEL,
    output logic [17:0] SELB,

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

    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) cnt <= 5'd0;
        else       cnt <= (cnt == 5'd19) ? 5'd0 : cnt + 5'd1;
    end

    assign swap = (cnt == 5'd19);

    assign PHI_C0 = (cnt <= 5'd1);
    assign PHI_C1 = (cnt >= 5'd2) && (cnt <= 5'd4);
    assign PHI_RA = (cnt >= 5'd5) && (cnt <= 5'd9);
    assign PHI_C2 = (cnt >= 5'd10) && (cnt <= 5'd17);
    assign PHI_AZ = (cnt >= 5'd4) && (cnt <= 5'd6);
    assign PRE    = (cnt <= 5'd1);
    assign HOLD   = (cnt >= 5'd18) || (cnt <= 5'd0);
    assign EN_RA  = PHI_RA;

    SliceSched u_sched (
        .clk(CLK200), .rstn(RSTN), .swap(swap),
        .acq(ACQ), .conv(CONV), .en(EN), .sel(SEL), .selb(SELB),
        .base(base), .m_act(m_act)
    );

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
