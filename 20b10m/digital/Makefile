SV = DigitalTop.sv SliceSched.sv Sar1Ctrl.sv Sar2Ctrl.sv Sinc2.sv ReconWeights.sv FramePack.sv SerLvds.sv

sim:
	iverilog -g2012 -o tb.out $(SV) tb_DigitalTop.sv && vvp tb.out

lint:
	iverilog -g2012 -Wall -o /dev/null $(SV) tb_DigitalTop.sv

clean:
	rm -f tb.out *.vcd
