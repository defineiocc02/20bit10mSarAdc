// ============================================================
// [CODE-INDEX] ReconWeights.sv —— 位重组 + 冻结系数（不是片上 LMS）
// 名义：DOUT = 0x200000 + (d1<<12) + ((d2-1024)<<3)，22 bit 偏移二进制。
// 校准：48 个系数由片外 LMS 训练后经 SPI 灌入；本文件只做“码 × 系数”。
// 注意：当前给名义权重；LMS 训练引擎不在片上，避免误读为自适应。
// ============================================================
// ReconWeights.sv —— 位重组 + 冻结权重（系数由片外 LMS 训练后经 SPI 灌入；片上不做自适应）
// DOUT = 22 bit 无符号偏移二进制，中心 0x200000，LSB = 0.5 LSB_total
`timescale 1ns/1ps

module ReconWeights (
    input  logic        clk,
    input  logic        rstn,
    input  logic [10:0] d1,
    input  logic [10:0] d2,
    input  logic        valid,
    output logic [21:0] dout
);

    // 名义：D1 权重 2^12，D2 权重 2^3（LSB2 = 8 u），中心 2^21
    wire signed [25:0] acc = ($signed({1'b0, d1}) <<< 12)
                           + (($signed({1'b0, d2}) - 26'sd1024) <<< 3);

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) dout <= 22'h200000;
        else if (valid) dout <= 22'h200000 + acc[21:0];
    end

endmodule
