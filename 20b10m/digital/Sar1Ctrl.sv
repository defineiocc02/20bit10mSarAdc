// ============================================================
// [CODE-INDEX] Sar1Ctrl.sv —— 一级：4b flash + 2b SAR + 5b 细搜
// 输入：coarse<14:0> 温度计、cmp 为 Cmp1 判决、ΦC0/ΦC1 窗口。
// 输出：D1<10:0>（10 bit + 1 位内部冗余占位）、SAMN 反相码。
// 注意：行为级，按 idx 递增取 cmp；不是 bit-exact 的 SAR 时序模型。
// ============================================================
// Sar1Ctrl.sv —— 一级：4b flash + 2b SAR + 5b 细搜（行为级，11 原始码）
`timescale 1ns/1ps

module Sar1Ctrl (
    input  logic        clk,
    input  logic        rstn,
    input  logic [14:0] coarse,        // 15 个比较器温度计码
    input  logic        cmp,           // Cmp1 判决
    input  logic        phi_c0,
    input  logic        phi_c1,
    output logic [10:0] d1,
    output logic [10:0] samn,
    output logic        done1
);

    logic [3:0] c4;
    logic [1:0] sar2;
    logic [4:0] fine;
    logic [2:0] idx;

    // 温度计 → 4 bit
    always_comb begin
        c4 = 4'd0;
        for (int i = 0; i < 15; i++) if (coarse[i]) c4 = c4 + 4'd1;
    end

    // ΦC0：4b 粗码 + 2 步 SAR
    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            sar2 <= 2'd0; idx <= 3'd0; done1 <= 1'b0;
        end else if (phi_c0) begin
            if (idx < 3'd2) begin
                sar2[idx] <= cmp;
                idx <= idx + 3'd1;
            end
        end else begin
            idx <= 3'd0;
            done1 <= 1'b0;
        end
    end

    // ΦC1：5 bit 细搜
    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) fine <= 5'd0;
        else if (phi_c1) begin
            if (idx < 3'd5) begin
                fine[4-idx] <= cmp;
                idx <= idx + 3'd1;
            end else begin
                done1 <= 1'b1;
            end
        end else begin
            idx <= 3'd0;
        end
    end

    // 10 bit 输出 + 1 位内部冗余（低 5 位细码，高 6 位粗码）
    assign d1 = {c4, sar2, fine[4:1], 1'b0};
    assign samn = ~d1;

endmodule
