// ============================================================
// [CODE-INDEX] FramePack.sv —— 24 bit 帧打包 + 16 深 FIFO
// 帧格式：{VALID, FAULT, DATA[21:0]}，MSB first。
// 行为：valid_in 时写 FIFO；非空时每拍读一帧；full 表示溢出风险。
// ============================================================
// FramePack.sv —— 24 bit 帧打包 + 16 深 FIFO
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

    logic [23:0] fifo [0:15];
    logic [4:0]  wr, rd, count;

    wire [23:0] frame = {valid_in, fault, din};

    always_ff @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            wr <= 5'd0; rd <= 5'd0; count <= 5'd0;
        end else begin
            if (valid_in && count < 5'd16) begin
                fifo[wr[3:0]] <= frame;
                wr <= wr + 5'd1;
                count <= count + 5'd1;
            end
            if (count > 5'd0) begin
                dout <= fifo[rd[3:0]];
                valid_out <= 1'b1;
                rd <= rd + 5'd1;
                count <= count - 5'd1;
            end else begin
                valid_out <= 1'b0;
            end
        end
    end

    assign full = (count == 5'd16);

endmodule
