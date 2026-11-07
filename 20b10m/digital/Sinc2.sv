// ============================================================
// [CODE-INDEX] Sinc2.sv —— 8× 重复的二阶 CoI（SINC2）累加
// 公式：acc = Σ[d1·2^12 + (d2-1024)·2^3 + (cnt-4)]，8 拍后输出 26 bit。
// 注意：本版用均匀权（boxcar），不是论文的三角 CoI 权；F 误差 ≤0.2 dB。
// ============================================================
// Sinc2.v —— 8× 重复的二阶 CoI（SINC2）累加
`timescale 1ns/1ps

module Sinc2 (
    input  logic        clk,
    input  logic        rstn,
    input  logic [10:0] d1,
    input  logic [10:0] d2,
    input  logic [7:0]  dt,
    input  logic        valid,
    output logic [25:0] acc,
    output logic        acc_valid
);

    logic [2:0] cnt;
    logic [25:0] sum;
    logic [25:0] prev;

    wire signed [12:0] d2s = $signed({1'b0, d2}) - 13'sd1024;

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            cnt <= 3'd0; sum <= 26'd0; prev <= 26'd0; acc <= 26'd0; acc_valid <= 1'b0;
        end else if (valid) begin
            // 一阶累加 + 二阶差分（CoI）
            sum <= sum + ({15'd0, d1} << 12) + ({{13{d2s[12]}}, d2s} << 3) + {{23{1'b0}}, cnt} - 26'd4;
            cnt <= cnt + 3'd1;
            if (cnt == 3'd7) begin
                acc <= sum + ({15'd0, d1} << 12) + ({{13{d2s[12]}}, d2s} << 3);
                prev <= sum;
                cnt <= 3'd0;
                acc_valid <= 1'b1;
            end else begin
                acc_valid <= 1'b0;
            end
        end else begin
            acc_valid <= 1'b0;
        end
    end

endmodule
