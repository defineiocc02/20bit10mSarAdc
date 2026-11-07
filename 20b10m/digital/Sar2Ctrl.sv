// ============================================================
// [CODE-INDEX] Sar2Ctrl.sv —— 二级：11 bit SAR + 8× LSB repeating
// 时序：ΦC2 内先 11 拍（idx 10→0），再 8 拍重复（rep 0→7）。
// 输出：D2<10:0>、DT<7:0>（DT[7:1] 反馈 7 个单位电容，DT[0] 作 LSB 判决）。
// 注意：行为级；未建模比较器亚稳态、DAC2 建立、replica 偏斜。
// ============================================================
// Sar2Ctrl.sv —— 二级：11 bit SAR + 8× LSB repeating
`timescale 1ns/1ps

module Sar2Ctrl (
    input  logic        clk,
    input  logic        rstn,
    input  logic        cmp2,
    input  logic        phi_c2,
    output logic [10:0] d2,
    output logic [7:0]  dt,
    output logic        done2
);

    logic [3:0] idx;
    logic [2:0] rep;

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            d2 <= 11'd0; dt <= 8'd0; idx <= 4'd10; rep <= 3'd0; done2 <= 1'b0;
        end else if (phi_c2) begin
            if (idx > 4'd0) begin
                d2[idx] <= cmp2;
                idx <= idx - 4'd1;
            end else begin
                // 8× 重复：DT[7:1] 反馈 7 个单位电容，DT[0] 作 LSB 判决
                if (rep < 3'd7) begin
                    dt[7-rep] <= cmp2;
                    rep <= rep + 3'd1;
                end else begin
                    dt[0] <= cmp2;
                    done2 <= 1'b1;
                end
            end
        end else begin
            idx <= 4'd10;
            rep <= 3'd0;
            done2 <= 1'b0;
        end
    end

endmodule
