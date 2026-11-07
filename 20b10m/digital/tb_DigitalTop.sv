// tb_DigitalTop.sv —— 数字顶层烟测：时钟/复位 + 固定 D1/D2 码流
`timescale 1ns/1ps

module tb_DigitalTop;
    logic CLK200 = 0;
    logic RSTN = 0;
    logic [10:0] D1 = 11'd512;
    logic [10:0] D2 = 11'd1024;
    logic [7:0]  DT = 8'h00;
    logic DONE1 = 0, DONE2 = 0;
    logic [14:0] COARSE = 15'h7FFF;
    logic [17:0] ACQ, CONV, EN, SEL, SELB;
    logic PHI_C0, PHI_C1, PHI_RA, PHI_AZ, PHI_C2, PRE, HOLD, EN_RA;
    logic [21:0] DOUT;
    logic DOUT_RDY;
    logic [7:0] MON;

    DigitalTop dut (.*, .VDD18(1'b1), .GND(1'b0));

    always #2.5 CLK200 = ~CLK200;   // 200 MHz

    initial begin
        #20 RSTN = 1;
        repeat (40) begin
            @(posedge CLK200);
            if (dut.cnt == 5'd17) DONE2 <= 1'b1; else DONE2 <= 1'b0;
        end
        #200 $finish;
    end

    initial begin
        $monitor("t=%0t cnt=%0d sel=%h dout=%h rdy=%b", $time, dut.cnt, SEL, DOUT, DOUT_RDY);
    end
endmodule
