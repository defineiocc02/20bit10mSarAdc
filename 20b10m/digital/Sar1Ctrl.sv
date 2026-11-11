// ============================================================
// [CODE-INDEX] Sar1Ctrl.sv —— 一级 4b flash + 2b SAR + 4b 细搜（10 bit，SSOT #2）
// 修订 T03（基线 BL-v1-draft / spec/ARCH_V2.md）：改为「相位包络 + 自定时」两域结构。
//
// 为什么必须两域（不是风格选择，是算术）：
//   ΦC0 = cnt 0–1 = 10 ns，ΦC1 = cnt 2–4 = 15 ns（SSOT #12）。
//   若位循环跑在 200 MHz 上升沿（5 ns/轮），6 轮 = 30 ns > 25 ns 包络 → 装不进。
//   故位循环不用 clk：时钟 = cmp_ready（比较器就绪，~2 ns/轮），clk 只做包络/看门狗/锁存。
//   见 interface/DIGITAL_ARCH.md §3.1「数字只负责包络的起止与超时计数」。
//
// 位序（MSB first）：
//   rnd 0 → sar2[1]，rnd 1 → sar2[0]，rnd 2..5 → fine[3..0]
//   d1 = {c4[3:0], sar2[1:0], fine[3:0]}  ← 10 bit，4 + 2 + 4
//
// 本文件**未经编译/仿真**（本机无 iverilog/verilator/yosys），只做了静态检查，
// 检查项与无法确认的风险见 digital/LINT_REPORT.md。
// ============================================================
`timescale 1ns/1ps

module Sar1Ctrl #(
    // 包络越界看门狗：env_act 连续高超过这么多 clk 还没完成 → fault。
    // 用途是兜住「包络不落」（计数器坏了 / 测试模式 phi 常高），**不是**逐拍看 ready。
    // 为什么不用「距上一个 cmp_ready 沿超过 N 拍」的看门狗：ready 是 ~2.1 ns 周期的窄脉冲，
    // 用 5 ns 采样它本身就是欠采样，连续 4 拍采不到完全正常 → 会误报。
    // 真正的超时判据是「包络落了还没完成」，见 S_CHK。
    parameter int TO_MAX_CYC   = 8,   // 40 ns（名义包络 25 ns 的 1.6 倍）
    // 完成判定的同步余量：包络结束后再等几个 clk 才判「没完成」。
    // 必须 ≥2，因为 c1_ok 到 clk 域要过 2 级同步器（2 clk = 10 ns）。
    parameter int TO_SYNC_CYC  = 2
) (
    input  logic        clk,          // 200 MHz：只做包络/超时/锁存
    input  logic        rstn,         // 异步置位、同步释放（复位同步器在壳层）
    input  logic [14:0] coarse,       // CmpCoarse4b 温度计码，ΦC0 内有效
    input  logic        cmp,          // Cmp1 判决；必须在 cmp_ready 上升前 ≥t_su 稳定
    input  logic        cmp_ready,    // Cmp1 就绪；自定时环的事件时钟（脉冲式，见 A-IF2）
    input  logic        phi_c0,       // 相位包络（不是判决时钟）
    input  logic        phi_c1,
    output logic [9:0]  d1,           // 偏移二进制：{c4, sar2, fine[3:0]}
    output logic [9:0]  samn,         // 反相码，给 DAC1 底板
    output logic        cmp_start,    // 请求下一次比较（4 相握手）
    output logic        done1,        // **1 拍脉冲**（5 ns），不是电平
    output logic        fault,        // 超时/卡死，粘到下一帧 ΦC0 上升沿
    output logic [3:0]  obs_rnd       // 调试观测 {c0_ok, rnd}（可悬空）
);

    // ---------------- 常量 ----------------
    localparam int NR_C0  = 2;        // ΦC0 内 Cmp1 判决轮数（2b SAR）
    localparam int NR_C1  = 4;        // ΦC1 内细搜轮数（4b fine）
    localparam int NR_ALL = NR_C0 + NR_C1;   // 6

    // ---------------- 组合：温度计 → 4 bit ----------------
    logic [3:0] c4;
    always_comb begin
        c4 = 4'd0;
        for (int i = 0; i < 15; i++) if (coarse[i]) c4 = c4 + 4'd1;
    end

    // 包络使能：直接用电平做「门」，不做 2FF 同步（使能门控不是数据通路，
    // 若加 2 clk 同步会吃掉 ΦC0 的 10 ns 预算）。数据本身不经此路。
    wire env_act = phi_c0 | phi_c1;

    // ============================================================
    // 域 A：自定时位循环（唯一状态机；时钟 = cmp_ready）
    // abort 为异步复位（clk 域产生，异步置位）：卡死/超时/帧尾都靠它把环打回 0。
    // 数据（sar2/fine）在 abort 时**不清**，保留给后仿定位；每帧 7 轮会全覆写。
    // ============================================================
    logic [2:0] rnd;
    logic [1:0] sar2;
    logic [3:0] fine;
    logic       c0_ok, c1_ok;         // 单调上升标志，交给域 B 做 2FF 同步
    logic       abort;                // 域 B 产生

    always_ff @(posedge cmp_ready or negedge rstn or posedge abort) begin
        if (!rstn) begin
            rnd   <= 3'd0;
            sar2  <= 2'd0;
            fine  <= 4'd0;
            c0_ok <= 1'b0;
            c1_ok <= 1'b0;
        end else if (abort) begin
            rnd   <= 3'd0;
            c0_ok <= 1'b0;
            c1_ok <= 1'b0;
        end else if (env_act && !c1_ok && (rnd < 3'(NR_ALL))) begin
            if (rnd < NR_C0) begin
                // 2b SAR：第 1 轮定 MSB
                sar2[(NR_C0-1)-rnd] <= cmp;
                rnd  <= rnd + 3'd1;
                if (rnd == 3'(NR_C0-1)) c0_ok <= 1'b1;
            end else begin
                // 4b 细搜：MSB first，rnd=5 落 fine[0]
                fine[(NR_ALL-1)-rnd] <= cmp;
                rnd  <= rnd + 3'd1;
                if (rnd == 3'(NR_ALL-1)) c1_ok <= 1'b1;
            end
        end
    end

    assign obs_rnd = {c0_ok, rnd};   // [3]=C0 两轮已完成，[2:0]=当前轮次（可悬空）

    // 4 相握手：只要在环内、还没做完、且还没看到 ready，就请求下一次比较。
    // 模拟侧契约：START↑ → READY↑ → START↓ → READY↓（READY 必须是脉冲，见 A-IF2）。
    assign cmp_start = env_act & ~c1_ok & ~abort & ~cmp_ready;

    // ============================================================
    // 域 B：200 MHz —— 包络判定 / 停顿看门狗 / 输出锁存
    // ============================================================
    typedef enum logic [2:0] {
        S_IDLE  = 3'd0,   // 等本帧包络上升
        S_RUN   = 3'd1,   // 包络内，位循环在跑
        S_CHK   = 3'd2,   // 包络已落，等 2 clk 同步余量再判完成
        S_DONE  = 3'd3,   // 已完成，done1=1，等包络落
        S_FAULT = 3'd4    // 超时/卡死，fault=1，done1 强制 1（不让下游挂住）
    } st_t;

    st_t        st;
    // 只同步 c1_ok：这是唯一的完成判据。c0_ok 不外同步——2FF 延迟（10 ns）
    // 与 ΦC0 包络（10 ns）同量级，在 RTL 里判「C0 是否在包络内完成」不可靠；
    // 改为把 c0_ok 原样导出到 obs_rnd[3]，交由断言/tb 在外部检查（见 LINT_REPORT §4.7）。
    logic [1:0] c1_sync;              // 2FF 同步器（域 A → 域 B）
    logic [3:0] env_cnt;              // env_act 已持续几个 clk（看门狗）
    logic [1:0] chk_cnt;              // S_CHK 内的等待计数
    logic       env_d;                // 包络延迟，用来取上升沿
    logic [3:0] c4_r;

    wire env_rise = env_act & ~env_d;

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            st        <= S_IDLE;
            c1_sync   <= 2'b00;
            env_cnt   <= 4'd0;
            chk_cnt   <= 2'd0;
            env_d     <= 1'b0;
            c4_r      <= 4'd0;
            d1        <= 10'd0;
            done1     <= 1'b0;
            fault     <= 1'b0;
            abort     <= 1'b1;        // 复位期间把自定时环钉死
        end else begin
            // ---- 2FF 同步（域 A → 域 B），单调上升标志 ----
            c1_sync <= {c1_sync[0], c1_ok};
            env_d   <= env_act;

            // ---- ΦC0 期间持续锁 c4，包络落时冻住最后一个有效值 ----
            // 若 CmpCoarse4b 需要 STROBE 而不是「ΦC0 内自然建立」，见 A-IF1。
            if (phi_c0) c4_r <= c4;

            // ---- done1 是 **1 拍脉冲**，不是电平 ----
            // 电平式 done 会让下游累加器（Sinc2）连续计多拍；这里默认清 0，
            // 下面 case 里若命中完成/超时才在**同一沿**把它置 1（后赋值覆盖前者）。
            done1 <= 1'b0;

            case (st)
                // ------------------------------------------------
                S_IDLE: begin
                    // abort 只在帧尾当 1 拍清环脉冲用：帧间不保持，
                    // 否则放环要等 1 clk（5 ns），会把 ΦC0 的 10 ns 吃掉一半。
                    // 帧间环不动是靠 env_act 门控，不是靠 abort。
                    if (env_rise) begin
                        fault   <= 1'b0;    // 新帧清故障
                        abort   <= 1'b0;
                        env_cnt <= 4'd0;
                        st      <= S_RUN;
                    end else begin
                        abort   <= 1'b0;
                        done1   <= 1'b0;
                        env_cnt <= 4'd0;
                    end
                end

                // ------------------------------------------------
                S_RUN: begin
                    abort <= 1'b0;
                    // 优先级：完成 > 包络落 > 包络越界（同沿只有一个动作落地）
                    if (c1_sync[1]) begin
                        // 完成早于包络结束（正常路径）
                        d1      <= {c4_r, sar2, fine[3:0]};
                        done1   <= 1'b1;
                        env_cnt <= 4'd0;
                        st      <= S_DONE;
                    end else if (!env_act) begin
                        chk_cnt <= 2'd0;
                        st      <= S_CHK;
                    end else if (env_cnt >= 4'(TO_MAX_CYC-1)) begin
                        done1 <= 1'b1;      // 只在进 S_FAULT 那一拍打脉冲
                        st    <= S_FAULT;   // 包络一直不落 → 兜底
                    end else begin
                        env_cnt <= env_cnt + 4'd1;
                    end
                end

                // ------------------------------------------------
                // 包络已落：给 2FF 同步器补 TO_SYNC_CYC 拍再判死刑，
                // 否则同步延迟（10 ns）会把「刚好赶上」误判成超时。
                S_CHK: begin
                    if (c1_sync[1]) begin
                        d1    <= {c4_r, sar2, fine[3:0]};
                        done1 <= 1'b1;
                        st    <= S_DONE;
                    end else if (chk_cnt >= 2'(TO_SYNC_CYC-1)) begin
                        done1 <= 1'b1;
                        st    <= S_FAULT;
                    end else begin
                        chk_cnt <= chk_cnt + 2'd1;
                    end
                end

                // ------------------------------------------------
                S_DONE: begin
                    abort <= 1'b1;        // 环已做完，钉住防止多打拍
                    if (!env_act) st <= S_IDLE;
                end

                // ------------------------------------------------
                S_FAULT: begin
                    abort <= 1'b1;
                    fault <= 1'b1;        // 粘到下一帧 ΦC0 上升沿
                    // done1 的脉冲在「进 S_FAULT 的那一拍」已经打过（见 S_RUN/S_CHK），
                    // 这里不再反复置位，否则会变成电平。
                    // 部分码也锁出来（后仿定位用），fault 已置位，语义为「无效样本」
                    d1 <= {c4_r, sar2, fine[3:0]};
                    if (!env_act) st <= S_IDLE;
                end
                default: st <= S_IDLE;
            endcase
        end
    end

    assign samn = ~d1;

endmodule
