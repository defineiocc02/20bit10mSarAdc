// ============================================================
// [CODE-INDEX] ReconWeights.sv —— 位重组 + 冻结系数（不是片上 LMS）
// 名义：DOUT = 0x200000 + ((d1-512)<<12) + ((d2-2048)<<2)，22 bit 偏移二进制。
// 口径：SSOT #7/#8；20.00 bit，1 LSB_total = 4 传输 LSB；D1/D2 都是偏移二进制。
// 校准：48 个系数由片外 LMS 训练后经 SPI 灌入；本文件只做“码 × 系数”。
// 注意：当前给名义权重；LMS 训练引擎不在片上，避免误读为自适应。
// ============================================================
`timescale 1ns/1ps

module ReconWeights (
    input  logic        clk,
    input  logic        rstn,
    input  logic [9:0]  d1,
    input  logic [11:0] d2,
    input  logic        valid,
    output logic [21:0] dout
);

    // D1 中码 512、D2 中码 2048 对应零输入；两者都必须先减偏置再乘权重。
    wire signed [27:0] acc = (($signed({1'b0, d1}) - 28'sd512) <<< 12)
                           + (($signed({1'b0, d2}) - 28'sd2048) <<< 2);

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) dout <= 22'h200000;
        else if (valid) dout <= 22'h200000 + acc[21:0];
    end

endmodule
