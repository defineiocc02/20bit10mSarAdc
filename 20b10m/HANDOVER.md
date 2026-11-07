# 交接文档 —— SAR20-10M（20.5 bit / 10 MS/s 两步式 SAR）

> 版本：2026-11-08　｜　交接人：上一轮会话　｜　接手人：待定
> 本文件是**唯一入口**：先读它，再按 §10 的检查表动手。深度内容看 §11 的文件地图。

---

## 0. 30 秒摘要

| 事项 | 状态 |
|:---|:---|
| 架构 | **已冻结**：10b DT 一阶 + 32×RA + 11b CT 二阶 + TA8，18 片 DAC1 池做 ADI 9.8 式**部分交织**到 10 MS/s |
| 行为级模型 | **可用**：14 个文件 2105 行 Python，64 张图，`selftest` 4 项全过；口径已按审计修正 |
| 模拟网表 | **层次完整、不可仿真**：28 个 .scs 参与编译（analog 下共 32）/ 220 实例 / 39 subckt / `check_hier.py` OK，但 `pdk_models.scs` 未填工艺模型 |
| 数字 RTL | **未编译、有 4 个功能性 bug**：本机无 iverilog/verilator，只做过端口文本比对 |
| 版图 | **无**。面积是自底向上估算（core 0.70–1.0 mm²），没有 floorplan 之外的任何版图工作 |
| 证据等级 | 只有 **L1（数值模型）+ L0（静态审计）**。没有综合、没有后仿、没有硅测 |
| 最大风险 | 数字侧「校准链路两条腿都断」：无系数写入口、无采集通路 → 片外 LMS 无处落地 |

**一句话**：模拟/架构/模型这条线可以往下走（改网表填 PDK、补非理想项）；数字这条线必须先修 bug、补 SPI 和采集通路，否则整个校准方案是空的。

---

## 1. 坐标

| 项 | 值 |
|:---|:---|
| 工作目录 | `/Users/zhaoyi/WorkBuddy/pipelinedsar工作站/20b10m/`（37 MB） |
| 远端仓库 | `git@github.com:defineiocc02/20bit10mSarAdc.git`（main） |
| 远端最新提交 | `886e214`（figs: 噪声分解/DR 曲线/SNDR-f 重做）｜ 前一提交 `cfb9bee`（模型口径修正） |
| 参考实现 | `defineiocc02/20bit_SAR_ADC_Behaviour_Verification` 分支 `20b10mtask`；本地 clone 在 `/Users/zhaoyi/src/20bit_SAR_ADC_Behaviour_Verification`（已 fetch 出该分支，工作树已清理） |
| Python | 3.13.12（`~/.workbuddy/binaries/python/versions/3.13.12/bin/python3`），numpy 2.5.4 / matplotlib 3.11.2 |
| EDA | **本机无 iverilog / verilator / yosys**。Spectre / Calibre / Virtuoso 在另一套环境，未在本机验证 |
| 对标论文 | 成电 CICC2026（`~/Desktop/13-6_Jin.pdf`）、ADI ISSCC2024 9.8、PKU VLSI2025 CAAZ |

---

## 2. 已冻结的口径（改之前先找人确认）

| 项 | 值 | 出处 |
|:---|:---|:---|
| 分辨率 / 速率 | 20.5 bit / 10 MS/s | `README.md` §2 |
| 位账 | 20.5 = 10(一级) + 11(二级) + 1.5(8×) − 2(冗余) | `spec/` |
| 满量程 | 差分 10 Vpp；28 pF/侧/样本（8 × 3.456 pF） | `params.py`、`spec/` |
| LSB | LSB1 = 9.766 mV，LSB2 = 19.07 µV，LSB_total = 6.744 µV | `params.py:32-34` |
| 级间增益 | G = 32 | `plan/arch_10m.md` |
| 帧时序 | 90 ns 转换 / 100 ns 周期；ΦC0 7.5 / ΦC1 15 / ΦRA 25 / ΦC2 37.5 / guard 5 | `README.md` §1、`DigitalTop.sv:60-68` |
| 交织 | 18 片池 = 8 转换 + 8 采集 + 2 备用；每 100 ns 换角色 | `SliceSched.sv` |
| 时钟 | 外部 200 MHz 差分，**无 PLL**；σt 目标 0.5 ps / 验收 1.0 ps | `plan/arch_10m.md` |
| 基准 | 外部 5 V / 2.5 V，片内 buffer | `analog/blocks/RefBuffer` |
| 输出 | 22 bit 无符号偏移二进制；LVDS DDR 400 Mbit/s；24 bit 帧 {VALID,FAULT,DATA[21:0]} | `interface/OUTPUT_IF_10M.md` |
| 封装 | QFN-48 6×6，48 pad（29 功能 + 19 电源地） | `interface/PINOUT_QFN48.md` |
| 校准 | **片外 LMS**（PC/测试机），片内只做「系数 × 码」的冻结重构 | `digital/README.md:46` |

⚠️ 最后一条有个坑：`ReconWeights.sv` 的头注释也这么写，但**实现里根本没有系数入口**，见 §6-D1。

---

## 3. 交付物清单与成熟度

成熟度分级：**A** 完整可用 ｜ **B** 存在且自洽、未验证 ｜ **C** 骨架/占位 ｜ **D** 缺失

| 类别 | 内容 | 数量 | 级 | 说明 |
|:---|:---|:---:|:---:|:---|
| 架构/规划 | `plan/` 14 份（arch_10m、coarse_quant_decision、area_model、area_vs_cicc、floorplan_4mm、routing_plan…） | 14 | A | 决策有取舍记录，可与 CICC 面积对标 |
| 规格 | `spec/` 6 份（spec_tree_10m、位分配、时序…） | 6 | B | 与 plan 有少量口径未收敛（§6-D7） |
| 接口 | `interface/` 16 份（引脚 48/32、输出协议、时序图） | 16 | A | 引脚图与 floorplan 图已出 PNG |
| 模拟网表 | `analog/netlist/` + `blocks/*/netlist/`：28 个 .scs 参与编译，220 实例 / 39 subckt | 32 | B | 层次/端口自洽（`check_hier.py` OK），**PDK 未填 → 不能仿真** |
| 模拟块规格 | `analog/blocks/*/spec.md` 25 个块 | 25 | B | 每块有 spec/ netlist/ sim/ reports/ layout/ 目录骨架 |
| 数字 RTL | `digital/*.sv` 9 个模块 + tb | 9 | **C** | **未编译**；4 个功能性 bug（§6） |
| 行为模型 | `model/*.py` 14 个文件 2105 行 | 14 | A | 口径经审计修正，`selftest` 全过 |
| 图 | 41 诊断 + 14 论文风格 + 9 实测风格 + 6 版图/引脚/时序 + 其他 | **75 PNG**（+SVG/PDF 共 200+） | A | 三套模型图各有 `manifest.json`（含 SHA256），PNG/SVG/PDF 同源 |
| 结论文档 | `TECH_EFFECTIVENESS.md`（152 行）、`model/REFERENCE_AUDIT.md`（274 行）、`digital/CALIBRATION_GAP.md`（427 行） | 3 | A | 这是本轮最有价值的产出 |

---

## 4. 结论：能声称 / 不能声称

完整版见 `TECH_EFFECTIVENESS.md`。摘要：

**能声称（有模型证据）**
1. DAC1 位权校准是 20 bit 的**必要条件**：不校准 SNDR 94.5 dB / SFDR 103.5 dBc，校准后回噪声底 101.8 dB（+7.3 dB）。
2. 级间增益校准第二重要：50 ppm 增益误差 = −5.4 dB。
3. CAAZ 净收益 +3.62 dB，其中**独家只有 0.58 dB**，其余 3.04 dB 是任何两点平均都有的。
4. 部分交织在 DR/SFDR 上是 **0.00 dB**，收益全在吞吐。
5. 洗牌：DR −1.0 dB 换 SFDR **+21.2 dBc**。
6. 校准残差 ∝ 1/√n：n=1 → 2.3 ppm，n=256 → 0.14 ppm；判据 ≤1.5 ppm 即可进噪声底 0.5 dB。

**只能声称方向**
- 8× tracking 的 +1.67 dB（区间 +0.88 ~ +2.76，取决于相关性机理）。
- CAAZ 的 +3.62 dB（依赖未标定的 AZ 共享度）。
- 任何绝对 SNDR（模型缺参考建立/亚稳态/DAC 建立，实测必然更低）。

**不能声称**
- "校准后 INL = 0"（数学假象，实际是有限样本残差）。
- "交织提高 SNR"（本架构下不成立）。
- "SFDR 137 dBc"（模型无失真项，无物理意义；预期实测 100–110 dBc）。
- 任何面积/功耗之外的 signoff 级结论。

---

## 5. 证据等级（别把 L1 当 signoff）

| 级 | 含义 | 当前状态 |
|:---|:---|:---|
| L0 | 静态审计 / 文本比对 | ✅ 已做（端口、层次、代码审查） |
| L1 | 数值行为模型 | ✅ 已做（本轮修正后口径自洽） |
| L2 | RTL 编译 + 仿真 | ❌ 未做（无工具，且有 4 个 bug） |
| L3 | 网表 Spectre 仿真 | ❌ 未做（PDK 未填） |
| L4 | 综合/后仿 | ❌ 未做 |
| L5 | 硅测 | ❌ 无 |

---

## 6. 已知缺陷清单

### P0（不做就没法往下走）

**D1　ReconWeights 没有系数写入口，且注释与实现不符**
`digital/ReconWeights.sv:1-6` 写着"48 个系数由片外 LMS 训练后经 SPI 灌入"，但 `:21-27` 只有两个写死的移位常数（D1 `<<12`、D2 `<<3`），没有系数端口、没有寄存器、没有 SPI。
→ 片外 LMS 的结果**无处可灌**。动作：加 `cfg_we`/`cfg_addr`/`cfg_data` 或直接上 SPI slave，见 `CALIBRATION_GAP.md` §4。

**D2　数字顶层没有校准/采集通路**
`DigitalTop.sv:15-47` 共 26 个端口，没有 `SPI_*`/`CAL_EN`/`CAL_DONE`/`TEST_MODE`/原始码导出；`SerLvds` **从未例化**（`grep SerLvds DigitalTop.sv` 无匹配）。
→ 片外 LMS 既拿不到训练数据，也灌不进结果。动作：见 `CALIBRATION_GAP.md` §3 的"必须补"三条。

**D3　Sar1Ctrl 两个 always_ff 抢同一个 idx**
`digital/Sar1Ctrl.sv:36-44`（粗量化阶段）与 `:49-61`（细搜阶段）都对 `idx` 赋值。综合会报多驱动，仿真行为不确定。
→ 动作：合并成一个状态机，或用 `stage` 选择分支。

**D4　Sar2Ctrl 需要的 tick 数超过 ΦC2 给的窗**
`Sar2Ctrl.sv:25-44` 需要 11（idx 10→0）+ 8（rep）= **19 个 ΦC2 tick**；而 `DigitalTop.sv:64` 的 `PHI_C2 = cnt∈[10,17]` 只有 **8 个**。且 `!phi_c2` 分支把 `idx` 复位成 10（`:41`），所以永远走不到 `done2`。
→ 动作：要么把 ΦC2 拉长到 19 tick（但 90 ns 帧装不下，需重新分配时序），要么把 8× 重复改成并行/流水。

### P1（功能不对，但可以先绕过）

**D5　FramePack 的 count 在同一 always_ff 里被 +1 和 −1 双写**
`FramePack.sv:33` 写 `count <= count + 1`，`:38` 又写 `count <= count - 1`（同一拍），后者覆盖前者 → 同时读写时计数不动。
→ 动作：改成 `nxt = count + wren - rden` 单次赋值。

**D6　Sinc2 的累加结果被丢掉**
`DigitalTop.sv:76-81` 声明 `acc` 并接到 Sinc2，但 `:85-88` 的重构用的是原始 `D1/D2`，`acc` 从未参与。
→ 8× 重复的收益在数字侧**没有真正实现**，模型里的 +1.67 dB 是模拟侧假设。动作：明确 8× 到底在模拟域还是数字域做，然后二选一改通。

**D7　系数个数口径未收敛：40 / 48 / 144**
`plan/` 预留 40 槽，`digital/README.md:46` 说 48，`CALIBRATION_GAP.md` 按 18 片 × 7 位 + 18 段增益算出 **144**。
→ 这不是笔误：**DAC1 到底是"单一 1023+16 单位阵列"还是"18 片独立池"在三份 plan 里有三种互斥写法**。冻结物理结构之前，"要多少个系数"无法定。这是最该先开的会。

**D8　RTL 从未编译**
本机无 iverilog/verilator/yosys；`analog/netlist/check_ports.py` 只做端口名/位宽的文本比对（26 vs 26 OK），不代表语法正确。
→ 动作：装 Icarus 或 Verilator（用户 Windows 机上有 Icarus 12.0），先把 9 个 .sv 编过再谈功能。

### P2（欠账，不阻塞）

**D9　`analog/netlist/pdk_models.scs` 只有填写说明，没有 include。** 网表不能直接跑 Spectre。文件里已经写明约束：不许用理想 MOS 代替（会把 L1 结论变假）。

**D10　模型缺 5 类非理想**：参考纹波/建立、比较器亚稳态、DAC 建立、开关电荷注入、采样网络带宽。已有：噪声（kT/C、RA 宽带、RA AZ、比较器、基准）、DAC1 静态 INL、在环 ADC2 量化（本轮补）、时钟抖动（本轮补，默认 0）。

**D11　16.4 ppm 依赖"同一阵列互补开关"假设。** 若 P/N 是独立阵列，量级回到 ~23 ppm（见 `REFERENCE_AUDIT.md` §1-4）。对外引用这个数必须带上前提。

**D12　洗牌在 RTL 里做不了。** `SliceSched.sv:16-22` 只输出 18 bit 掩码 + base，没有**有序**的 5 bit slice id，重建无法知道这一拍用了哪 8 片、什么顺序。模型里"洗牌 +21 dBc"的结论目前无 RTL 支撑。

**D13　面积没经过任何版图验证。** core 0.70–1.0 mm² 是自底向上算的（`analog/area_model.md`），对标 CICC 的 0.53 mm² 反推 MIM 密度 2 fF/µm²。4 mm² 是宽松版。

---

## 7. 模型口径与踩过的坑（别再踩一遍）

1. **矩形窗必须严格相干。** `metrics.fft_metrics` 现在有硬断言：fin 偏 0.25 bin 时 SNDR 会从 102 dB 掉到 **13.8 dB**，而且不报错。所有实验都要先 `round(fin*N/fs)*fs/N`。
2. **DNL 必须用同一条拟合直线的斜率归一。** 用标称 LSB1 会产生 `mean(DNL)=+2.23 ppm` 的不自洽（INL 用最佳直线、DNL 用标称，两者对不上）。
3. **校准残差不是 0。** 理想 0 只在"INL 恰由位权误差张成 + 权重无限准"时成立。现在用 `cal_residual(n_avg)` 给有限样本残差（∝1/√n）。任何"校准后 INL=0"的图都是错的。
4. **静态模型有两套拓扑，别混用。** `static.curves()` 默认走本项目拓扑（8 unary × 128，INL 16.4 ppm）；`curves_binary()` 是旧的单端 10 bit 二进制（38.6 ppm），差 2.3 倍。
5. **AR(1) 沿"重复次数 m"递推是我的假设，不是参考实现的做法。** 参考里没有 M 次平均机制。引用 +1.67 dB 要带区间。
6. **字体**：`font.family` 必须写成列表（`["Hiragino Sans GB","Arial","DejaVu Sans"]`），否则 µ 和 − 会变成方框；mathtext 的 `\mathdefault` 解析不到列表，所以对数轴统一换成纯文本刻度（`viz._plain_log_axes`）。
7. **标题定位用毫米不用百分比**（`viz.annotate`）：74 mm 高的图上，百分比定位会让标题压住副标题。
8. **`model/plots.py` 曾经写进 `results/figures/`，把 41 图 manifest 覆盖成 5 条**（已改成写 `results/figures_plots/`）。如果发现 `figures/manifest.json` 里只有 5 个文件名，说明被 plots.py 覆盖了，重跑 `python3 -m model.figures` 即可恢复。
9. **出图必须用 ViewImage 真看。** 只看脚本输出 "wrote N figures" 会漏掉标题被裁、文字压曲线、刻度 1e+02 偏移这类问题（本轮就漏过三次）。

---

## 8. 命令手册

```bash
cd 20b10m

# 模型（约 1 分钟全跑完）
python3 -m model.selftest           # 4 项自检，必须全 PASS
python3 -m model.experiments        # 重算 results/results.json + report.md（6 s）
python3 -m model.figures            # 41 张诊断图（28 s）
python3 -m model.paper_figures      # 14 张论文风格图
python3 -m model.measured_figures   # 9 张实测风格图（13 s，含 DR/SNDR-f 扫描）
python3 -m model.plots              # 15 个旧格式文件（兼容用）

# 模拟侧自检
python3 analog/netlist/check_hier.py    # 层次/实例数
python3 analog/netlist/check_ports.py   # 数字↔模拟端口文本比对（26 vs 26）

# 推送（SSH 通道，已配好）
rsync -a --delete --exclude='.git' ./ /tmp/20bit10mSarAdc/20b10m/
cd /tmp/20bit10mSarAdc && git add -A && git commit -m "..." && git push origin main
```

⚠️ `/tmp/20bit10mSarAdc` 是临时克隆，随时可能被清掉；丢了就重新 `git clone git@github.com:defineiocc02/20bit10mSarAdc.git`，仓库里已有完整内容。

---

## 9. 下一步（建议里程碑，按依赖排序）

| 里程碑 | 内容 | 验收标准 | 依赖 |
|:---|:---|:---|:---|
| **M0** | 冻结 DAC1 物理结构（单一阵列 or 18 片池），同步 40/48/144 三个口径 | 三份 plan 说法一致；系数个数确定 | 需要架构评审，1 次会 |
| **M1** | 修 D3/D4/D5/D6，装 Icarus/Verilator，9 个 .sv 编过 + `tb_DigitalTop` 跑通 | `iverilog -g2012` 零 warning；tb 输出 1 帧正确数据 | M0 |
| **M2** | 加 SPI 系数写入口 + 校准采集模式（原始码 + slice id） | 片外能读回 144 组码、能回灌权重；回灌后重构码与模型一致 | M1 |
| **M3** | 填 `pdk_models.scs`，网表跑通 DC/AC/瞬态（每个块一个 testbench） | 25 个块至少 top + DAC1 + RA + CT2 有仿真结果 | 需要 PDK 环境 |
| **M4** | 补模型缺的 5 类非理想（D10），重跑全部图 | 图注里的"未建模"逐条销账 | 可与 M1–M3 并行 |

**不建议现在做的**：版图。面积还没被任何仿真校准过（RA 噪声、DAC1 单位电容、参考 buffer 驱动能力都是预算值），先做版图会返工。

---

## 10. 接手检查表

**第一小时**
- [ ] `cd 20b10m && python3 -m model.selftest` → 4 项 PASS
- [ ] 读 `TECH_EFFECTIVENESS.md`（152 行）——这是全部结论
- [ ] 读本文件 §6 的 P0 四条，确认你认同优先级
- [ ] `git -C /tmp/20bit10mSarAdc log --oneline -5` 确认远端与本地一致

**第一天**
- [ ] 随机抽 3 张图，用看图工具打开，对照 `manifest.json` 的 SHA256（确认图不是旧的）
- [ ] 读 `model/REFERENCE_AUDIT.md` §3「能声称/不能声称」，和 `TECH_EFFECTIVENESS.md` §4 对一遍
- [ ] 打开 `digital/Sar1Ctrl.sv`，自己确认 `idx` 是不是真的被两个 always 驱动（别信文档，信代码）
- [ ] 决定 M0 的会什么时候开

**第一个坑预警**
- 改模型参数前先看 `params.py` 头部的注释（哪些是实测、哪些是反解推断）。ρ=0.61 是**反解值，不是实测**。
- 改 RTL 前先确认有没有仿真工具，否则你改完也不知道对不对。

---

## 11. 文件地图

```
20b10m/
├── README.md                 工程总览（112 行）
├── HANDOVER.md               本文件
├── TECH_EFFECTIVENESS.md     ★ 各技术有效性对比（结论总表）
├── PLAN.md                   WBS / 门禁 G0–G6 / 排期
├── CODE_INDEX.md             代码索引（带行数）
├── FILE_LAYOUT.md            文件存放规范
├── plan/                     14 份：架构裁决、粗量化决策、面积模型、面积对标、floorplan、走线
├── spec/                     6 份：规格树、位分配、时序
├── interface/                16 份：引脚 48/32、输出协议、时序图（含 PNG）
├── analog/
│   ├── blocks/               25 个块，每块 spec.md + netlist/ sim/ reports/ layout/
│   ├── netlist/              28 个 .scs（build.scs 是编译根）、check_hier.py、check_ports.py
│   ├── area_model.md         自底向上面积
│   ├── area_vs_cicc.md       与 CICC 0.53 mm² 对标（反推 MIM 2 fF/µm²）
│   ├── floorplan_4mm.md      部分交织版图布局 + PNG
│   └── routing_plan.md       从 CICC die photo 识别的走线规则
├── digital/
│   ├── *.sv                  9 个模块 + tb（未编译）
│   ├── CALIBRATION_GAP.md    ★ 校准链路缺口（427 行，带 file:line）
│   └── README.md             数字侧说明（注意 :46 的 48 系数说法与实现不符）
├── model/
│   ├── *.py                  14 个文件 2105 行
│   ├── REFERENCE_AUDIT.md    ★ 与参考实现逐点对照（274 行）
│   ├── AUDIT.md              早期的可信度说明
│   ├── PLOT_DESIGN.md        出图规范
│   └── results/              results.json / report.md / figures{,_paper,_measured}/ + manifest
├── verilog/                  端口桩
├── review/                   评审记录
└── docs/ skill/              导入步骤、建库脚本
```

带 ★ 的三份是本轮核心产出，其余是支撑材料。
