// ============================================================
// [CODE-INDEX] SliceSched.sv —— 18 片池调度（8 转换 + 8 采样 + 2 备）
// 规则：conv = mask8(base)，acq = mask8(base+8)；base 每次 swap +8 mod 18。
//       9 次换相覆盖全部 18 片；每片周期 200 ns（100 采样 + 90 转换 + 10 空闲）。
// 端口：swap 每 100 ns 一个脉冲；sel=conv 给 SliceMux；en=conv|acq。
// 局限：轮换而非 LFSR/DEM 洗牌；没有 stall/ID 冻结（参考库有，本版简化）。
// ============================================================
// SliceSched.sv —— 18 片池调度（部分交织：8 转换 + 8 采样 + 2 备）
// 角色每 100 ns 交换一次；base 每次 +8 mod 18，9 次换相覆盖全部 18 片。
`timescale 1ns/1ps

module SliceSched (
    input  logic        clk,
    input  logic        rstn,
    input  logic        swap,          // 每 100 ns 一个脉冲
    output logic [17:0] acq,           // 采样组（8 片）
    output logic [17:0] conv,          // 转换组（8 片）
    output logic [17:0] en,            // 16 片使能，2 片备用
    output logic [17:0] sel,           // 送 SliceMux（=conv）
    output logic [17:0] selb,
    output logic [4:0]  base,
    output logic [3:0]  m_act
);

    function automatic [17:0] mask8(input int start);
        int idx;
        mask8 = 18'd0;
        for (int k = 0; k < 8; k++) begin
            idx = (start + k) % 18;
            mask8[idx] = 1'b1;
        end
    endfunction

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) base <= 5'd0;
        else if (swap) base <= (base + 5'd8) % 5'd18;
    end

    always_comb begin
        conv = mask8(base);
        acq  = mask8(base + 8);
        en   = conv | acq;
        sel  = conv;
        selb = ~sel;
        m_act = 4'd8;
    end

endmodule
