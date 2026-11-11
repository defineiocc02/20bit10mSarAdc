// ============================================================
// [CODE-INDEX] Sar2Ctrl.sv —— 二级 12 bit SAR + 8× LSB 重复（SSOT #5/#30）
// 修订 T03（基线 BL-v1-draft / spec/ARCH_V2.md）：改为「相位包络 + 自定时」两域结构。
//
// 轮次账（共 20 轮，SSOT #5：D2 = 12 bit）：
//   rnd  0..11 → d2[11..0]  （12 bit，MSB first）
//   rnd 12..19 → dt[7..0]   （8× 重复，模拟域读 8 次，数字只锁 8 个判决做平均）
//   第 20 轮（rnd=19，落 dt[0]）完成时置 loop_ok。
//
// **拍数约束**：ΦC2 包络 = cnt 9–17 = 9 tick = 45 ns（SSOT #12）；
//   20 轮 / 45 ns = 2.25 ns/轮；Cmp2 指标 ≤2.0 ns/拍，余 0.25 ns。
//
// 本文件**未经编译/仿真**（本机无 iverilog/verilator/yosys），只做了静态检查。
// ============================================================
`timescale 1ns/1ps

module Sar2Ctrl #(
    // 包络越界看门狗：env_act 连续高超过这么多 clk 还没完成 → fault。
    // 兜的是「包络不落」，**不是**逐拍看 ready：ready 是 ~2.1 ns 窄脉冲，
    // 用 5 ns 采样本身欠采样，按"连续 N 拍没沿"判会误报。见 Sar1Ctrl 同处注释。
    parameter int TO_MAX_CYC   = 11,  // 55 ns（名义包络 45 ns 的 1.22 倍）
    // 包络落后等几拍再判超时（≥2 = 2FF 同步余量）
    parameter int TO_SYNC_CYC  = 2
) (
    input  logic        clk,          // 200 MHz：只做包络/超时/锁存
    input  logic        rstn,         // 异步置位、同步释放
    input  logic        cmp2,         // Cmp2 判决；cmp_ready 上升前沿已稳定
    input  logic        cmp_ready,    // Cmp2 就绪；自定时环的事件时钟（脉冲式，A-IF2）
    input  logic        phi_c2,       // 相位包络（不是判决时钟）
    output logic [11:0] d2,           // 12 bit 偏移二进制
    output logic [7:0]  dt,           // 8× 重复码（8 个判决，1 bit/次）
    output logic        cmp_start,    // 请求下一次比较
    output logic        done2,        // **1 拍脉冲**（5 ns），不是电平
    output logic        fault,        // 超时/卡死，粘到下一帧 ΦC2 上升沿
    output logic [4:0]  obs_rnd       // 调试观测：当前轮次 0..18（可悬空）
);

    // ---------------- 常量 ----------------
    localparam int NB_D2   = 12;      // 12 bit SAR
    localparam int NB_REP  = 8;       // 8× 重复
    localparam int NR_ALL  = NB_D2 + NB_REP;   // 20

    wire env_act = phi_c2;

    // ============================================================
    // 域 A：自定时位循环（唯一状态机；时钟 = cmp_ready）
    // ============================================================
    logic [4:0] rnd;                  // 0..19，5 bit
    logic [11:0] d2_raw;
    logic [7:0]  dt_raw;
    logic        loop_ok;             // 单调上升，交给域 B 做 2FF 同步
    logic        abort;

    always_ff @(posedge cmp_ready or negedge rstn or posedge abort) begin
        if (!rstn) begin
            rnd     <= 5'd0;
            d2_raw  <= 12'd0;
            dt_raw  <= 8'd0;
            loop_ok <= 1'b0;
        end else if (abort) begin
            rnd     <= 5'd0;
            loop_ok <= 1'b0;          // 数据保留给后仿定位
        end else if (env_act && !loop_ok && (rnd < 5'(NR_ALL))) begin
            if (rnd < 5'(NB_D2)) begin
                // 12 bit SAR，MSB first；rnd=11 落 d2[0]
                d2_raw[(NB_D2-1)-rnd] <= cmp2;
                rnd <= rnd + 5'd1;
            end else begin
                // 8× 重复：rep = rnd-12 ∈ 0..7 → dt[7]..dt[0]
                dt_raw[(NB_REP-1)-(rnd-5'(NB_D2))] <= cmp2;
                if (rnd == 5'(NR_ALL-1)) loop_ok <= 1'b1;
                rnd <= rnd + 5'd1;
            end
        end
    end

    assign obs_rnd = rnd;

    assign cmp_start = env_act & ~loop_ok & ~abort & ~cmp_ready;

    // ============================================================
    // 域 B：200 MHz —— 包络判定 / 包络越界看门狗 / 输出锁存
    // d2/dt 在 clk 域寄存：loop_ok 到 clk 域要过 2 级同步器（10 ns），
    // 因此 d2/dt 在 done2 上升前已稳定 ≥10 ns，下游按 done2 采样无 CDC 风险。
    // ============================================================
    typedef enum logic [2:0] {
        S_IDLE  = 3'd0,
        S_RUN   = 3'd1,
        S_CHK   = 3'd2,
        S_DONE  = 3'd3,
        S_FAULT = 3'd4
    } st_t;

    st_t        st;
    logic [1:0] ok_sync;
    logic [3:0] env_cnt;              // env_act 已持续几个 clk（看门狗）
    logic [1:0] chk_cnt;
    logic       env_d;

    wire env_rise = env_act & ~env_d;

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            st        <= S_IDLE;
            ok_sync   <= 2'b00;
            env_cnt   <= 4'd0;
            chk_cnt   <= 2'd0;
            env_d     <= 1'b0;
            d2        <= 12'd0;
            dt        <= 8'd0;
            done2     <= 1'b0;
            fault     <= 1'b0;
            abort     <= 1'b1;
        end else begin
            ok_sync <= {ok_sync[0], loop_ok};
            env_d   <= env_act;

            // done2 是 **1 拍脉冲**，不是电平：Sinc2 这类累加器按脉冲计数，
            // 电平式 done2 会让它一拍一拍连续累加同一个样本。
            done2 <= 1'b0;

            case (st)
                // ------------------------------------------------
                S_IDLE: begin
                    if (env_rise) begin
                        fault   <= 1'b0;
                        abort   <= 1'b0;
                        env_cnt <= 4'd0;
                        st      <= S_RUN;
                    end else begin
                        abort   <= 1'b0;   // 帧间只留 1 拍清环脉冲
                        done2   <= 1'b0;
                        env_cnt <= 4'd0;
                    end
                end

                // ------------------------------------------------
                S_RUN: begin
                    abort <= 1'b0;
                    if (ok_sync[1]) begin
                        d2      <= d2_raw;     // 环已停在稳定值，一次锁存
                        dt      <= dt_raw;
                        done2   <= 1'b1;
                        env_cnt <= 4'd0;
                        st      <= S_DONE;
                    end else if (!env_act) begin
                        chk_cnt <= 2'd0;
                        st      <= S_CHK;
                    end else if (env_cnt >= 4'(TO_MAX_CYC-1)) begin
                        done2 <= 1'b1;     // 强制完成（1 拍脉冲），避免下游挂住
                        st    <= S_FAULT;
                    end else begin
                        env_cnt <= env_cnt + 4'd1;
                    end
                end

                // ------------------------------------------------
                // 包络落后补 TO_SYNC_CYC 拍：这是同步延迟补偿，不是放水。
                // 注意：20 轮在 45 ns 内的余量只有 0.25 ns/拍，SS 角需重点复核。
                S_CHK: begin
                    if (ok_sync[1]) begin
                        d2    <= d2_raw;
                        dt    <= dt_raw;
                        done2 <= 1'b1;
                        st    <= S_DONE;
                    end else if (chk_cnt >= 2'(TO_SYNC_CYC-1)) begin
                        done2 <= 1'b1;   // 超时也强制给 1 拍 done2，但 fault=1
                        st    <= S_FAULT;
                    end else begin
                        chk_cnt <= chk_cnt + 2'd1;
                    end
                end

                // ------------------------------------------------
                S_DONE: begin
                    abort <= 1'b1;
                    // done2 的脉冲已在进 S_DONE 的那一拍打过（S_RUN/S_CHK），此处不重复
                    if (!env_act) st <= S_IDLE;
                end

                // ------------------------------------------------
                S_FAULT: begin
                    abort <= 1'b1;
                    fault <= 1'b1;
                    // done2 的 1 拍脉冲在进 S_FAULT 那拍已打（见 S_RUN/S_CHK）
                    // 不锁 d2_raw/dt_raw：超时样本的码值无意义，锁出来会被误当数据。
                    // 若后仿要定位，从 obs_rnd 读停在哪一轮。
                    if (!env_act) st <= S_IDLE;
                end

                default: st <= S_IDLE;
            endcase
        end
    end

endmodule
