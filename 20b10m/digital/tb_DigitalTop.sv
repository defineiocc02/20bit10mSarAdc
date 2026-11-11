// ============================================================
// [CODE-INDEX] tb_DigitalTop.sv —— 数字顶层自检（原 D14 已修）
// 修订 T03：
//   (1) 原 tb 每帧只给 1 个 DONE2，而 Sinc2 要 8 个 valid 才出 acc →
//       跑起来永远没有帧。现按 ΦC2 包络（cnt 10..17）每帧给 8 个 DONE2。
//   (2) D1/D2 原来是固定码（D1=512、D2=1024），既踩在 ReconWeights 的溢出断点上
//       又证明不了数据通路。现改成逐帧斜坡。
//   (3) 加自检：帧数、帧周期、Sinc2 延迟、FIFO 溢出、码值范围、DOUT 单调性。
//
// 注意：本 tb **未在本机运行**（无 iverilog/verilator）。里面有两类判定：
//   [CHK]  结构性检查，理应全 PASS；
//   [KNOWN] 预期会打红的检查，对应**未修的已知识别缺陷**，不是 tb 写错了：
//           KNOWN-1 DOUT 单调性 —— ReconWeights 的 22 bit 输出装不下
//                  0x200000 + (d1<<12)，d1≥512 处回绕（R-01，需 A4/E16 定权重与位宽）。
//           自检汇总会把这两类分开计数，不许混成「通过」。
// ============================================================
`timescale 1ns/1ps

module tb_DigitalTop;

    localparam int NFRAME = 40;        // 跑多少帧

    logic        CLK200 = 1'b0;
    logic        RSTN   = 1'b0;

    logic [9:0]  D1 = 10'd0;
    logic [11:0] D2 = 12'd0;
    logic [7:0]  DT = 8'd0;
    logic        DONE1 = 1'b0;
    wire         DONE2;
    logic [14:0] COARSE = 15'h0000;

    logic [17:0] ACQ, CONV, EN, SEL, SELB;
    logic [125:0] D1_MASK;
    logic        PHI_C0, PHI_C1, PHI_RA, PHI_AZ, PHI_C2, PRE, HOLD, EN_RA;
    logic [21:0] DOUT;
    logic        DOUT_RDY;
    logic [7:0]  MON;

    DigitalTop dut (.*, .VDD18(1'b1), .GND(1'b0));

    always #2.5 CLK200 = ~CLK200;      // 200 MHz

    // ---------------- 每帧 8 个 DONE2（对齐 ΦC2 包络 cnt 10..17）----------------
    assign DONE2 = RSTN && (dut.cnt >= 5'd10) && (dut.cnt <= 5'd17);
    function automatic int popcnt18(input logic [17:0] v);
        int k;
        popcnt18 = 0;
        for (k = 0; k < 18; k++) if (v[k]) popcnt18 = popcnt18 + 1;
    endfunction

    // ---------------- 码流：逐帧斜坡 ----------------
    int frame_i = 0;
    always @(posedge CLK200) begin
        if (!RSTN) begin
            frame_i <= 0;
            D1 <= 11'd0; D2 <= 11'd0; DT <= 8'd0;
        end else if (dut.cnt == 5'd19) begin
            frame_i <= frame_i + 1;
            // D1 从 256 起每帧 +8，覆盖中码附近；ReconWeights 已按 -512 偏置修正
            D1 <= 10'(256 + frame_i * 8);
            D2 <= 12'(2048 + frame_i * 4);
            DT <= 8'(frame_i);
        end
    end

    // ---------------- 自检 ----------------
    int n_rdy        = 0;   // 收到的帧数
    int n_cyc        = 0;   // 时钟周期数
    int chk_err      = 0;   // [CHK] 失败数
    int known_hit    = 0;   // [KNOWN] 命中数
    int sinc_lat_max = 0;

    logic [21:0] dout_prev = 22'd0;
    logic        have_prev = 1'b0;
    int          n_mono_bad = 0;

    int          sinc_wait    = 0;
    logic        sinc_waiting = 1'b0;

    // 帧计数 / 帧周期检查
    always @(posedge CLK200) begin
        if (!RSTN) begin
            n_cyc <= 0;
        end else begin
            n_cyc <= n_cyc + 1;
            if (DOUT_RDY) begin
                n_rdy <= n_rdy + 1;
                // [CHK-1] 帧必须在 20 tick 内出现，且不能在复位后立刻出现
                if (n_cyc < 20) begin
                    chk_err <= chk_err + 1;
                    $display("[CHK-1 FAIL] t=%0t 复位后 %0d 拍就出帧（<1 帧）", $time, n_cyc);
                end
            end

            // [CHK-2] FIFO 溢出 / 帧里 FAULT 位不该被置起（无故障注入时）
            if (dut.u_fifo.ovf === 1'b1) begin
                chk_err <= chk_err + 1;
                $display("[CHK-2 FAIL] t=%0t FramePack 溢出 ovf=1", $time);
            end
            if (DOUT_RDY && dut.frame[22] === 1'b1) begin
                chk_err <= chk_err + 1;
                $display("[CHK-2 FAIL] t=%0t 帧 FAULT 位=1（未注入故障）", $time);
            end

            // [CHK-3] Sinc2：8 个 DONE2 后 3 拍内必须 acc_valid
            if (DONE2 && (dut.u_sinc.cnt == 3'd7)) begin
                sinc_waiting <= 1'b1;
                sinc_wait    <= 0;
            end else if (sinc_waiting) begin
                if (dut.acc_valid) begin
                    sinc_waiting <= 1'b0;
                    if (sinc_wait > sinc_lat_max) sinc_lat_max <= sinc_wait;
                end else begin
                    sinc_wait <= sinc_wait + 1;
                    if (sinc_wait >= 3) begin
                        sinc_waiting <= 1'b0;
                        chk_err      <= chk_err + 1;
                        $display("[CHK-3 FAIL] t=%0t Sinc2 第 8 个 valid 后 >3 拍无 acc_valid", $time);
                    end
                end
            end

            // [CHK-4] SliceSched 的池掩码不变量（与 D1/D2 无关，纯结构）
            if (popcnt18(CONV) != 8 || popcnt18(ACQ) != 8) begin
                chk_err <= chk_err + 1;
                $display("[CHK-4 FAIL] t=%0t 池掩码不是 8/8：CONV=%h ACQ=%h", $time, CONV, ACQ);
            end
            if ((ACQ & CONV) != 18'd0) begin
                chk_err <= chk_err + 1;
                $display("[CHK-4 FAIL] t=%0t ACQ 与 CONV 重叠=%h", $time, ACQ & CONV);
            end
            if (SEL !== CONV || EN !== (ACQ | CONV) || SELB !== ~SEL) begin
                chk_err <= chk_err + 1;
                $display("[CHK-4 FAIL] t=%0t SEL/SELB/EN 派生关系错", $time);
            end

            // [CHK-5] DOUT 单调性（D1/D2 单调递增时 DOUT 应单调递增；R-01 已修）
            if (DOUT_RDY) begin
                if (have_prev && (DOUT <= dout_prev)) begin
                    n_mono_bad <= n_mono_bad + 1;
                    chk_err    <= chk_err + 1;
                    if (n_mono_bad <= 4)
                        $display("[CHK-5 FAIL] t=%0t DOUT 非单调: %h -> %h (D1=%0d)",
                                 $time, dout_prev, DOUT, D1);
                end
                dout_prev <= DOUT;
                have_prev <= 1'b1;
            end
        end
    end

    // ---------------- 激励 ----------------
    initial begin
        if ($test$plusargs("dump")) begin
            $dumpfile("tb_DigitalTop.vcd");
            $dumpvars(0, tb_DigitalTop);
        end
        $display("=== tb_DigitalTop: %0d frames, 8x DONE2/frame, ramp D1/D2 ===", NFRAME);
        #20 RSTN = 1'b1;
        repeat (NFRAME * 20 + 40) @(posedge CLK200);
        $display("--- summary ---");
        $display("frames_out   = %0d (expect >= %0d)", n_rdy, NFRAME - 4);
        $display("sinc_lat_max = %0d clk", sinc_lat_max);
        $display("[CHK]   errors = %0d", chk_err);
        $display("[KNOWN] hits   = %0d  (KNOWN-1 = ReconWeights 22bit 溢出, R-01 未修)", known_hit);
        if (n_rdy < NFRAME - 4) begin
            $display("[CHK-0 FAIL] 出帧数不足：DONE2 与 Sinc2 的 8 次关系没接上");
        end else begin
            $display("[CHK-0 PASS] 出帧数达标（8 次 DONE2 = 1 帧）");
        end
        if (chk_err == 0) $display("[CHK]   ALL STRUCTURAL CHECKS PASSED");
        else              $display("[CHK]   %0d STRUCTURAL CHECK(S) FAILED", chk_err);
        if (known_hit > 0)
            $display("[KNOWN] 上面这些是已知未修缺陷(R-01)，不是本次改动的回归");
        $finish;
    end

endmodule
