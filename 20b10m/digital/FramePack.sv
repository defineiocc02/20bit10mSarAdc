// ============================================================
// [CODE-INDEX] FramePack.sv —— 24 bit 帧打包 + 16 深 FIFO
// 修订 T03：修掉原 D5 —— `count` 在同拍被 +1 与 −1 两次非阻塞赋值，后者覆盖前者
//   （原 FramePack.sv:33 与 :38），导致「写进去的那一帧数不出来」，帧数恒少。
//   现改为组合算 nxt = count + wr_en − rd_en，再用单次赋值落地（唯一驱动点）。
// 另外补上溢出语义：FIFO 满还来写 → 置粘性 ovf，并入帧的 FAULT 位
//   （原实现 `full` 只在端口上挂着，帧里没有任何溢出痕迹）。
// 端口未变（DigitalTop 的 26 端口与 digital_stubs.scs 不受影响）。
// 本文件**未经编译/仿真**，静态检查见 digital/LINT_REPORT.md。
// ============================================================
// 帧：{VALID, FAULT, DATA[21:0]}，MSB first
`timescale 1ns/1ps

module FramePack (
    input  logic        clk,
    input  logic        rstn,
    input  logic [21:0] din,
    input  logic        valid_in,
    input  logic        fault,
    output logic [23:0] dout,
    output logic        valid_out,
    output logic        full
);

    localparam int DEPTH = 16;

    logic [23:0] fifo [0:DEPTH-1];
    logic [4:0]  wr, rd, count;
    logic        ovf;                 // 粘性溢出标志

    // ---- 读写使能 ----
    wire wr_en = valid_in && (count < 5'(DEPTH));
    wire rd_en = (count > 5'd0);
    wire ovf_now = valid_in && (count == 5'(DEPTH));   // 满了还写

    // ---- 唯一一次 count 赋值（原 D5 的修法）----
    logic [4:0] nxt;
    always_comb begin
        nxt = count;
        if (wr_en) nxt = nxt + 5'd1;
        if (rd_en) nxt = nxt - 5'd1;
    end

    wire [23:0] frame = {valid_in, (fault | ovf | ovf_now), din};

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            wr        <= 5'd0;
            rd        <= 5'd0;
            count     <= 5'd0;
            dout      <= 24'd0;
            valid_out <= 1'b0;
            ovf       <= 1'b0;
        end else begin
            // 写口
            if (wr_en) begin
                fifo[wr[3:0]] <= frame;
                wr            <= wr + 5'd1;
            end
            // 读口：非空即读，每拍出一帧
            if (rd_en) begin
                dout      <= fifo[rd[3:0]];
                valid_out <= 1'b1;
                rd        <= rd + 5'd1;
            end else begin
                valid_out <= 1'b0;
            end
            // 计数：一次落地，不再被后面的分支覆盖
            count <= nxt;
            // 溢出：粘到清零（本版无独立清零口，随 rstn 清）
            if (ovf_now) ovf <= 1'b1;
        end
    end

    assign full = (count == 5'(DEPTH));

endmodule
