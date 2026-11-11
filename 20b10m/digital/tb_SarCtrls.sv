// ============================================================
// [CODE-INDEX] tb_SarCtrls.sv —— Sar1Ctrl / Sar2Ctrl 自定时环自检（T03 新增）
//
// 目的：DigitalTop 不例化 Sar1Ctrl/Sar2Ctrl（它们在 Sar1Top/Sar2Ct 的数字壳内），
//       所以 tb_DigitalTop 根本碰不到这两个模块。本 tb 直接驱动它们，验 4 件事：
//   1) 轮次账：Sar1 = 2+5 = 7 轮；Sar2 = 11 + 8 = 19 轮，且 d2[0]/dt[7:0] 全被写；
//   2) 位序：MSB first（用 rnd%3==0 的判决图样反推，若 LSB first 期望值不成立）；
//   3) 自定时：包络内 done 必须起来，fault 必须为 0；
//   4) 超时保护：比较器卡死 / 太慢时必须置 fault、并强制 done（不让下游挂住）。
//
// 4 个相位（按帧号切换 dly）：
//   frame 0..4  : dly=1.20 ns（≈1.25 ns/轮）→ 期望 PASS
//   frame 5..9  : dly=2.36 ns（ARCH_V2 §4 给的 Cmp2 指标）→ **期望 fault=1**
//                这不是 tb 出错，是在用 tb 复现 A-T1 的算术：
//                19 × 2.41 = 45.8 ns > ΦC2 的 40 ns 包络。
//   Sar1 同期把 ready 钉死 → 期望 fault=1（包络落 + 2 clk 的超时判定）。
//
// 期望值推导（cmp = (rnd%3==0)）：
//   Sar1: rnd0=1→sar2[1], rnd3=1→fine[3], rnd6=1→fine[0]
//         c4 = popcount(15'h7FFF) = 15
//         d1 = {4'hF, 2'b10, 4'b0100, 1'b0} = 11'h7C8（bit0 恒 0）
//   Sar2: rnd0=1→d2[10], rnd3=1→d2[7], rnd6=1→d2[4], rnd9=1→d2[1]
//         d2 = 11'h492
//         rnd12=1→dt[6], rnd15=1→dt[3], rnd18=1→dt[0]（dt 索引 7-(rnd-11)）
//         dt = 8'h49
//
// 本 tb **未在本机运行**（无 iverilog/verilator）。
// ============================================================
`timescale 1ns/1ps

module tb_SarCtrls;

    localparam int  NFRAME   = 10;
    localparam real DLY_FAST = 1.20;
    localparam real DLY_SLOW = 2.36;   // ARCH_V2 §4：Cmp2 = 2.36 ns/bit

    // ---------------- 公共时钟 / 帧包络 ----------------
    logic clk = 1'b0;
    logic rstn = 1'b0;
    logic [4:0] cnt = 5'd0;

    always #2.5 clk = ~clk;

    always @(posedge clk or negedge rstn) begin
        if (!rstn) cnt <= 5'd0;
        else       cnt <= (cnt == 5'd19) ? 5'd0 : cnt + 5'd1;
    end

    wire phi_c0 = (cnt <= 5'd1);
    wire phi_c1 = (cnt >= 5'd2)  && (cnt <= 5'd4);
    wire phi_c2 = (cnt >= 5'd10) && (cnt <= 5'd17);

    int frame = 0;
    always @(posedge clk) begin
        if (!rstn) frame <= 0;
        else if (cnt == 5'd19) frame <= frame + 1;
    end

    // ---------------- Sar1Ctrl ----------------
    logic [10:0] d1, samn;
    logic        cmp1, rdy1, start1, done1, fault1;
    logic [3:0]  rnd1;      // {c0_ok, rnd[2:0]}

    Sar1Ctrl u_sar1 (
        .clk(clk), .rstn(rstn),
        .coarse(15'h7FFF),
        .cmp(cmp1), .cmp_ready(rdy1),
        .phi_c0(phi_c0), .phi_c1(phi_c1),
        .d1(d1), .samn(samn),
        .cmp_start(start1), .done1(done1), .fault(fault1),
        .obs_rnd(rnd1)
    );

    // ---------------- Sar2Ctrl ----------------
    logic [10:0] d2;
    logic [7:0]  dt;
    logic        cmp2, rdy2, start2, done2, fault2;
    logic [4:0]  rnd2;

    Sar2Ctrl u_sar2 (
        .clk(clk), .rstn(rstn),
        .cmp2(cmp2), .cmp_ready(rdy2),
        .phi_c2(phi_c2),
        .d2(d2), .dt(dt),
        .cmp_start(start2), .done2(done2), .fault(fault2),
        .obs_rnd(rnd2)
    );

    // ---------------- 比较器模型（4 相握手 + 判决图样）----------------
    real dly1 = DLY_FAST;
    real dly2 = DLY_FAST;
    bit  stuck1 = 1'b0;     // 第一批帧之后把 Sar1 的比较器钉死，测超时判定
    bit  slow_ph = 1'b0;    // frame>=5 起进入「慢比较器」相位

    always @(posedge clk) begin
        if (frame == 5) begin
            slow_ph <= 1'b1;
            dly2    <= DLY_SLOW;
            stuck1  <= 1'b1;
        end
    end

    // Sar1 比较器：卡死模式下永不回 ready
    // 判决在 start 上升沿立刻给出（模拟侧契约：cmp 必须先于 ready 稳定），
    // 再等 dly 才回 ready —— 这样 start 边沿读到的 rnd 就是本轮编号，不会错位一拍。
    always @(posedge start1) begin
        if (!stuck1) begin
            cmp1 = (((rnd1[2:0]) % 3) == 0);   // 只看轮次位，rnd1[3] 是 c0_ok
            #(dly1);
            rdy1 = 1'b1;
            #0.05;
            rdy1 = 1'b0;
        end
    end

    // Sar2 比较器
    always @(posedge start2) begin
        cmp2 = ((rnd2 % 3) == 0);
        #(dly2);
        rdy2 = 1'b1;
        #0.05;
        rdy2 = 1'b0;
    end

    // ---------------- 采集与判定 ----------------
    int   n_d1_fast = 0, n_f1_fast = 0, n_f1_slow = 0;
    int   n_d2_fast = 0, n_f2_fast = 0, n_f2_slow = 0;
    logic c0_seen = 1'b0;    // obs_rnd[3]：C0 的两轮是否完成（RTL 内部判不了，只能外部看）
    logic [10:0] d1_snap = 11'hxxx;
    logic [10:0] d2_snap = 11'hxxx;
    logic [7:0]  dt_snap = 8'hxx;
    int   errs = 0;

    logic d1_q = 1'b0, d2_q = 1'b0, f1_q = 1'b0, f2_q = 1'b0;

    always @(posedge clk) begin
        d1_q <= done1;  d2_q <= done2;
        f1_q <= fault1; f2_q <= fault2;
        if (rnd1[3]) c0_seen <= 1'b1;   // C0 两轮完成过一次

        if (!slow_ph) begin
            if (done1 && !d1_q) begin n_d1_fast <= n_d1_fast + 1; d1_snap <= d1; end
            if (fault1 && !f1_q) n_f1_fast <= n_f1_fast + 1;
            if (done2 && !d2_q) begin
                n_d2_fast <= n_d2_fast + 1;
                d2_snap   <= d2;
                dt_snap   <= dt;
            end
            if (fault2 && !f2_q) n_f2_fast <= n_f2_fast + 1;
        end else begin
            if (fault1 && !f1_q) n_f1_slow <= n_f1_slow + 1;
            if (fault2 && !f2_q) n_f2_slow <= n_f2_slow + 1;
        end
    end

    // ---------------- 主流程 ----------------
    initial begin
        if ($test$plusargs("dump")) begin
            $dumpfile("tb_SarCtrls.vcd");
            $dumpvars(0, tb_SarCtrls);
        end
        $display("=== tb_SarCtrls: Sar1Ctrl 7 rounds / Sar2Ctrl 19 rounds, self-timed ===");
        #20 rstn = 1'b1;
        repeat (NFRAME * 20 + 40) @(posedge clk);

        $display("--- Sar1Ctrl ---");
        $display("  fast frames: done1 rises = %0d (expect >=4)", n_d1_fast);
        $display("  d1 snapshot = 11'h%h (expect 11'h7c8, bit0 must be 0)", d1_snap);
        $display("  fault in fast phase  = %0d (expect 0)", n_f1_fast);
        $display("  fault in stuck phase = %0d (expect >=1, stall watchdog)", n_f1_slow);
        $display("  obs_rnd[3] (c0_ok)   = %b (expect 1：C0 两轮完成过)", c0_seen);
        if (n_d1_fast < 4)  begin errs++; $display("  [FAIL] Sar1 包络内没完成"); end
        if (d1_snap !== 11'h7c8) begin
            errs++;
            $display("  [FAIL] d1 位映射错：MSB-first 期望 7c8。若为 3e4 一类说明是 LSB-first");
        end
        if (d1_snap[0] !== 1'b0) begin errs++; $display("  [FAIL] d1[0] 必须恒 0（D-03）"); end
        if (n_f1_fast != 0) begin errs++; $display("  [FAIL] 快相位不该报 fault"); end
        if (n_f1_slow < 1)  begin errs++; $display("  [FAIL] 比较器卡死没被抓到（超时判定失效）"); end
        if (!c0_seen)       begin errs++; $display("  [FAIL] C0 两轮从未完成（obs_rnd[3] 一直是 0）"); end

        $display("--- Sar2Ctrl ---");
        $display("  fast frames: done2 rises = %0d (expect >=4)", n_d2_fast);
        $display("  d2 snapshot = 11'h%h (expect 11'h492, 含 d2[0])", d2_snap);
        $display("  dt snapshot =  8'h%h  (expect   8'h49, 8 位全写到)", dt_snap);
        $display("  fault in fast phase = %0d (expect 0)", n_f2_fast);
        $display("  fault in slow phase = %0d (expect >=1 = A-T1 复现)", n_f2_slow);
        if (n_d2_fast < 4)  begin errs++; $display("  [FAIL] Sar2 包络内没完成"); end
        if (d2_snap !== 11'h492) begin
            errs++;
            $display("  [FAIL] d2 位映射错：期望 492（MSB-first + 11 位全落）");
        end
        if (dt_snap !== 8'h49) begin
            errs++;
            $display("  [FAIL] dt 未写满 8 位或位序错：期望 49（dt 索引 = 7-(rnd-11)）");
        end
        if (n_f2_fast != 0) begin errs++; $display("  [FAIL] 快相位不该报 fault"); end
        if (n_f2_slow < 1)  begin
            errs++;
            $display("  [FAIL] 慢比较器(dly=2.36ns)居然没超时 —— 说明包络判定失效");
        end else begin
            $display("  [NOTE] 慢相位报 fault 是**预期**：19x2.41=45.8ns > 40ns 包络（A-T1）");
        end

        if (errs == 0) $display("=== tb_SarCtrls: ALL GROUPS PASSED");
        else           $display("=== tb_SarCtrls: %0d GROUP(S) FAILED", errs);
        $finish;
    end

endmodule
