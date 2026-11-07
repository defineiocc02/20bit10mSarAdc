// ============================================================
// [CODE-INDEX] SerLvds.sv —— 24 bit 帧 → 400 Mbit/s DDR 串行
// 帧：{VALID,FAULT,DATA[21:0]}；帧长 60 ns，周期 100 ns；CLKOUT=200 MHz。
// 注意：双沿 always 块是行为级；综合时换 ODDR + 真 LVDS 驱动。
// ============================================================
// SerLvds.sv —— 24 bit 帧打包 + 400 Mbit/s DDR 串行器（行为级骨架）
// 帧格式：{VALID, FAULT, DATA[21:0]}，MSB first；帧长 60 ns，帧周期 100 ns。
// 说明：DDR 输出用双沿 always 块描述，仅用于仿真；综合时替换为 ODDR 原语 + 真 LVDS 驱动。
`timescale 1ns/1ps

module SerLvds (
    input  logic        CLK200,
    input  logic        RSTN,

    input  logic [21:0] DIN,
    input  logic        VALID,
    input  logic        FAULT,
    input  logic        SYNC_EN,

    output logic        DOUTP,
    output logic        DOUTN,
    output logic        CLKOUTP,
    output logic        CLKOUTN,
    output logic        DRDYP,
    output logic        DRDYN
);

    // 100 ns 帧计数（20 个 5 ns tick）
    logic [4:0] cnt;
    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) cnt <= 5'd0;
        else       cnt <= (cnt == 5'd19) ? 5'd0 : cnt + 5'd1;
    end

    // 256 帧一次 SYNC
    logic [7:0] frame_cnt;
    logic       sync_frame;
    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) begin frame_cnt <= 8'd0; sync_frame <= 1'b0; end
        else if (cnt == 5'd19) begin
            frame_cnt <= frame_cnt + 8'd1;
            sync_frame <= SYNC_EN && (frame_cnt == 8'hFF);
        end
    end

    // 帧装载
    logic [23:0] sh;
    logic        tx_bit;
    wire  [23:0] frame = sync_frame ? 24'hFFFFFF : {VALID, FAULT, DIN};

    always_ff @(posedge CLK200 or negedge RSTN) begin
        if (!RSTN) begin
            sh <= 24'd0; tx_bit <= 1'b0;
        end else if (cnt == 5'd0) begin
            sh <= frame;
            tx_bit <= frame[23];
        end else if (cnt <= 5'd11) begin
            sh <= {sh[21:0], 2'b00};
            tx_bit <= sh[22];          // 下降沿发下一位
        end
    end

    // 下降沿发奇数位（行为级；综合换 ODDR）
    always_ff @(negedge CLK200 or negedge RSTN) begin
        if (!RSTN) tx_bit <= 1'b0;
        else if ((cnt >= 5'd0) && (cnt <= 5'd11)) tx_bit <= sh[23];
    end

    // 输出
    assign DOUTP   = tx_bit;
    assign DOUTN   = ~tx_bit;
    assign CLKOUTP = CLK200;
    assign CLKOUTN = ~CLK200;
    assign DRDYP   = (cnt == 5'd0);
    assign DRDYN   = ~(cnt == 5'd0);

endmodule
