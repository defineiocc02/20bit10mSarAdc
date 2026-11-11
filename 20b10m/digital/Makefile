# ============================================================
# digital/Makefile —— 编译/检查命令模板（T03 更新）
#
# **本机没有 iverilog / verilator / yosys，下列目标均未真正跑过。**
# 命令是给有工具的环境用的；跑之前请先看 LINT_REPORT.md 里的「无法确认的风险」。
#
#   make tools      看本机有哪些工具
#   make lint       iverilog 语法 + 警告
#   make vlint      verilator --lint-only（更严，含 UNOPTFLAT/多驱动/位宽）
#   make sim        tb_DigitalTop（顶层数据通路，8x DONE2/帧）
#   make sim_ctrl   tb_SarCtrls（Sar1Ctrl/Sar2Ctrl 自定时环，含超时注入）
#   make check      Python 位映射复算（不需要仿真器，随时可跑）
#   make all        能跑的都跑
# ============================================================

IVERILOG ?= iverilog
VVP      ?= vvp
VERILATOR?= verilator
PYTHON   ?= python3

# DigitalTop 及其子模块
TOP_SV   = DigitalTop.sv SliceSched.sv Sinc2.sv ReconWeights.sv FramePack.sv
# 模拟壳内的两个自定时控制器（DigitalTop 不例化它们）
CTRL_SV  = Sar1Ctrl.sv Sar2Ctrl.sv
# 未例化但保留
MISC_SV  = SerLvds.sv

ALL_SV   = $(TOP_SV) $(CTRL_SV) $(MISC_SV)
TB_TOP   = tb_DigitalTop.sv
TB_CTRL  = tb_SarCtrls.sv

.PHONY: all tools lint vlint sim sim_ctrl check clean

all: check lint vlint sim sim_ctrl

tools:
	@echo "iverilog : $$(command -v $(IVERILOG) || echo 'NOT FOUND')"
	@echo "verilator: $$(command -v $(VERILATOR) || echo 'NOT FOUND')"
	@echo "yosys    : $$(command -v yosys || echo 'NOT FOUND')"
	@echo "python3  : $$(command -v $(PYTHON) || echo 'NOT FOUND')"

# ---- Python 位映射复算：不需要仿真器 ----
check:
	$(PYTHON) check_bitmap.py

# ---- iverilog 语法/警告 ----
lint:
	$(IVERILOG) -g2012 -Wall -o /dev/null $(ALL_SV) $(TB_TOP) $(TB_CTRL)

# ---- verilator lint（更严）----
# 说明：-Wno-DECLFILENAME 因为我们一个文件一个 module 但含中文注释；
#       Sar1/Sar2 的 posedge cmp_ready 会被报 UNOPTFLAT/异步时钟，那是自定时环的
#       固有结构（见 LINT_REPORT.md §2.4），不是要消掉的告警。
vlint:
	$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module DigitalTop $(TOP_SV)
	$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME \
		--top-module Sar1Ctrl Sar1Ctrl.sv
	$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME \
		--top-module Sar2Ctrl Sar2Ctrl.sv

# ---- 顶层数据通路烟测 ----
# 预期：CHK-0..4 全 PASS；KNOWN-1（DOUT 单调性）会命中若干次，
#       因为 ReconWeights 22 bit 溢出（R-01）本次未修。见 tb 文件头。
sim:
	$(IVERILOG) -g2012 -o tb_top.out $(TOP_SV) $(TB_TOP) && $(VVP) tb_top.out

# ---- 两个控制器的自定时/超时自检 ----
# 预期：sar1/sar2 快相位 PASS；慢相位（dly=2.36 ns）**故意**报 fault = A-T1 复现。
sim_ctrl:
	$(IVERILOG) -g2012 -o tb_ctrl.out $(CTRL_SV) $(TB_CTRL) && $(VVP) tb_ctrl.out

clean:
	rm -f tb_top.out tb_ctrl.out tb.out *.vcd
