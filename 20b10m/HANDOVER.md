# 交接文档 —— SAR20-10M（20.5 bit / 10 MS/s 两步式 SAR）

> 版本：**r2 / 2026-11-08**（按接手者视角重组；r1 原文存于 `git a7584c6`，本地备份 `/tmp/HANDOVER_r1_20261108.bak`）
> 本文件是**唯一入口**：先读 §0–§2，再按 §8 的检查表动手。深度内容看 §6 的文件地图与命令。
> 证据标记约定：`[复核]` = 本版整理时实际跑过/读过（L0 静态或 L1 运行）；`[原记录]` = 沿用上一轮结论，本轮未重跑。

---

## 0. 30 秒摘要

| 事项 | 状态 | 依据 |
|:---|:---|:---|
| 架构 | **已冻结**：10b DT 一阶 + 32×RA + 11b CT 二阶 + TA8；18 片 DAC1 池做 ADI 9.8 式**部分交织**到 10 MS/s | `plan/arch_10m.md` |
| 行为级模型 | **可用**：14 文件 2106 行 Python，64 张图（41+14+9），`selftest` 4 项全 PASS `[复核]` | 本轮实跑 |
| 模拟网表 | **层次完整、不可仿真**：28 个 .scs 参与编译 / 220 实例 / 39 subckt，`check_hier` 与 `check_ports` 均 OK `[复核]`；但 `pdk_models.scs` 未填工艺模型 | 本轮实跑 |
| 数字 RTL | **未编译、有 4 个功能性 bug**，且按现状**整条链不产出任何有效码** | §4.1 D1–D4 |
| 版图 | **无**。面积是自底向上估算（core 0.70–1.0 mm²），除 floorplan 文本外无任何版图工作 | `analog/area_model.md` |
| 证据等级 | 只有 **L1（数值模型）+ L0（静态审计）**。无综合、无前仿、无后仿、无硅测 | §2.3 |
| 最大风险 | 数字侧「校准链路两条腿都断」：无系数写入口、无采集通路 → 片外 LMS 无处落地 | `digital/CALIBRATION_GAP.md` |

**一句话**：模拟/架构/模型这条线可以往下走（填 PDK、补非理想项）；数字这条线必须先修 bug、补 SPI 与采集通路，否则整个校准方案是空的。

**接手前必须知道的三件事**
1. 根目录 `STATUS.md` 停留在 2026-11-07 的 G0 阶段，**已过时**，与本文冲突时以本文为准（见 §5.3）。
2. `20b10m/` 在本地**不受任何 git 仓库跟踪**，唯一权威副本是 GitHub `defineiocc02/20bit10mSarAdc`。
3. 数字 RTL 从未被任何编译器看过；本文对 RTL 的判断全部是**文本级静态复核**，不是仿真结论。

---

## 1. 任务目标

### 1.1 要做成什么

复现 CICC 2026（成电）20.5 bit / 5 MS/s 两级 SAR（CT 二阶 + tracking averaging），并用 ADI ISSCC2024 9.8 式的**部分交织**做到 **10 MS/s**：只交织 DAC1 的 18 片池，量化器 / RA / CT2 / 参考 / 数字全部单套共享。

```
VIN → 18 片 DAC1 池（8 转换 + 8 采样 + 2 备）
    → SliceMux(18:1，选 8 片) → RA → CT2(C_INC + DAC2 + replica) → DigitalTop → LVDS
```

### 1.2 冻结指标（改之前先找人确认）

| 项 | 值 | 出处 |
|:---|:---|:---|
| 分辨率 / 速率 | 20.5 bit / 10 MS/s | `README.md` §2 |
| 位账 | 20.5 = 10（一级）+ 11（二级）+ 1.5（8×）− 2（冗余） | `spec/` |
| 满量程 | 差分 10 Vpp；28 pF/侧/样本（8 × 3.456 pF） | `model/params.py`、`spec/` |
| LSB | LSB1 = 9.766 mV，LSB2 = 19.07 µV，LSB_total = 6.744 µV | `model/params.py:32-34` |
| 级间增益 | G = 32 | `plan/arch_10m.md` |
| 帧时序（规格） | 90 ns 转换 / 100 ns 周期；ΦC0 7.5 / ΦC1 15 / ΦRA 25 / ΦC2 37.5 / guard 5 | `README.md` §1 |
| 帧时序（RTL 实现） | 20 tick × 5 ns；ΦC0 0-1 / ΦC1 2-4 / ΦRA 5-9 / ΦC2 10-17 / cnt18-19 = HOLD+换相 `[复核]` | `digital/DigitalTop.sv:57-68` |
| 交织 | 18 片池 = 8 转换 + 8 采集 + 2 备用；每 100 ns 换角色，每片周期 200 ns | `digital/SliceSched.sv` |
| 时钟 | 外部 200 MHz 差分，**无 PLL**；σt 目标 0.5 ps / 验收 1.0 ps | `plan/arch_10m.md` |
| 基准 | 外部 5 V / 2.5 V，片内 buffer | `analog/blocks/RefBuffer` |
| 输出 | 22 bit 无符号偏移二进制；LVDS DDR 400 Mbit/s；24 bit 帧 {VALID, FAULT, DATA[21:0]} | `interface/OUTPUT_IF_10M.md` |
| 封装 | QFN-48 6×6，48 pad（29 功能 + 19 电源地） | `interface/PINOUT_QFN48.md` |
| 系统指标目标 | SNDR 99.4 dB @100 kHz / DR 102.5 dB / core 3.5–3.8 mW | `README.md`、`STATUS.md` |
| 面积 | 对标 CICC 0.53 mm² core / 0.79 mm² die；本项目自底向上估 **0.70–1.0 mm²**，4 mm² 宽松版 / 1.06 mm² 紧缩版 | `analog/area_vs_cicc.md` |
| 校准 | **片外 LMS**（PC/测试机），片内只做「系数 × 码」的冻结重构 | `digital/README.md:46` |

> ⚠️ 规格里的 7.5 / 37.5 ns 在 RTL 里被取整成 2 / 8 tick（10 / 40 ns），guard 5 ns 被 cnt18-19 的 HOLD 吸收。两套口径都对，但**对不上**——D4 的可行性判断必须用 RTL 口径（18 tick 转换窗）。

### 1.3 边界（本项目不做什么）

- P3 路线（换一级结构、ADI 式 sDAC + RDAC follower）**不在本项目**，见 `PLAN.md` §1。
- 片内不做 LMS 自适应；片上没有校准引擎。
- 现阶段不做版图（理由见 §7.3）。

---

## 2. 当前进展

### 2.1 一句话

架构、规格、模拟网表层次、行为模型四条线**已搭完并可自洽**；数字 RTL 是**未编译的骨架且功能不成立**；版图与所有仿真（前仿/后仿/综合）**为零**。

### 2.2 交付物成熟度

分级：**A** 完整可用 ｜ **B** 存在且自洽、未验证 ｜ **C** 骨架/占位 ｜ **D** 缺失

| 类别 | 内容 | 数量 | 级 | 说明 |
|:---|:---|:---:|:---:|:---|
| 架构/规划 | `plan/` 14 份（arch_10m、coarse_quant_decision、area_model、area_vs_cicc、floorplan_4mm、routing_plan…） | 14 | A | 决策有取舍记录，可与 CICC 面积对标 |
| 规格 | `spec/` 6 份（spec_tree_10m、位分配、时序…） | 6 | B | 与 plan 有少量口径未收敛（§5.3） |
| 接口 | `interface/` 16 份（引脚 48/32、输出协议、时序图） | 16 | A | 引脚图与 floorplan 图已出 PNG |
| 模拟网表 | `analog/netlist/` + `blocks/*/netlist/`：28 个 .scs 参与编译（analog 下共 32）、220 实例 / 39 subckt `[复核]` | 32 | B | 层次/端口自洽，**PDK 未填 → 不能仿真** |
| 模拟块规格 | `analog/blocks/*/spec.md` 25 个块 | 25 | B | 每块有 spec / netlist / sim / reports / layout 目录骨架 |
| 数字 RTL | `digital/*.sv` 9 个模块 + tb，共 498 行 `[复核]` | 9 | **C** | **未编译**；4 个功能性 bug（§4.1） |
| 行为模型 | `model/*.py` 14 个文件 2106 行 `[复核]` | 14 | A | 口径经审计修正，`selftest` 4/4 PASS `[复核]` |
| 图 | 64 张模型图（41 诊断 + 14 论文风格 + 9 实测风格）+ 5 旧格式 + 6 版图/引脚/时序 = **75 PNG** `[复核]` | 75 | A | 三套图各有 `manifest.json`（含 SHA256、figure_count），PNG/SVG/PDF 同源 |
| 结论文档 | `TECH_EFFECTIVENESS.md`(152 行)、`model/REFERENCE_AUDIT.md`(274)、`digital/CALIBRATION_GAP.md`(427) | 3 | A | 本轮最有价值的产出 |

### 2.3 证据等级（别把 L1 当 signoff）

| 级 | 含义 | 当前状态 |
|:---|:---|:---|
| L0 | 静态审计 / 文本比对 / 行号复核 | ✅ 已做（端口 26/26、层次 220 实例、RTL 走读、`git` 与图 manifest 核对） |
| L1 | 数值行为模型 | ✅ 已做（`selftest` 4/4，模型口径自洽） |
| L2 | RTL 编译 + 仿真 | ❌ 未做（本机无 iverilog/verilator/yosys，且有 4 个 bug） |
| L3 | 网表 Spectre 仿真 | ❌ 未做（`pdk_models.scs` 未填） |
| L4 | 综合 / 后仿 | ❌ 未做 |
| L5 | 硅测 | ❌ 无 |

### 2.4 与 G0–G6 门禁的映射（回答"我们到哪了"）

| Gate | 判据（`PLAN.md` §3） | 实际 | 差距 |
|:---|:---|:---|:---|
| G0 规格冻结 | 所有数字单一来源 | **未通过** | 系数个数 40/48/64/144 四套口径（D7） |
| G1 架构/模型 | 趋势可复现、有判据 | **基本通过** | tracking 区间未收敛（依赖 ρ 反解） |
| G2 模块设计 | 网表端口一致 + 单元仿真过判据 | **半通过** | 端口一致 ✅；**单元仿真 0 个** ❌；RTL 不成立 ❌ |
| G3 系统前仿 | DR 102.0–103.5、SNDR ≥97、90 ns 闭合 | **未开始** | 无 Spectre 环境 |
| G4 版图 | DRC/LVS 零错 | **未开始** | — |
| G5 后仿 | 相对前仿 DR −1.0 dB | **未开始** | — |
| G6 硅测 | DR ≥101.5 | **未开始** | — |

> 结论：项目处在 **G1 收尾 / G2 开头**，且 G2 被"没有仿真工具 + PDK 未填 + RTL 不成立"三件事同时卡住。

---

## 3. 已完成的部分

### 3.1 架构与规格（A）

- `plan/arch_10m.md`：10 MS/s 架构裁决、18 片池、时钟/基准/引脚、面积口径。
- `plan/coarse_quant_decision.md`：4b flash（15 cmp）+ 2b SAR 的粗量化取舍。
- `plan/interleaving_replan.md`：从 8 片到 18 片池的部分交织重规划（驱动带宽 20.3→22.3 MHz 的推导）。
- `analog/area_model.md` / `area_vs_cicc.md` / `floorplan_4mm.md` / `routing_plan.md`：面积自底向上、与 CICC 0.53 mm² 对标、4 mm² floorplan、走线规则。
- `spec/` 6 份：位账、时序预算、层次树、接口 CSV。

### 3.2 行为模型（A）

- 14 个文件覆盖 `params / sources / metrics / static / adc / charge_model / experiments / figures / paper_figures / measured_figures / plots / viz / selftest`。
- `python3 -m model.selftest` → **4/4 PASS** `[复核]`：
  `纯正弦 DR 268.0 dB` / `tracking 方差 emp/F=1.000` / `CAAZ az_share 扫描` / `静态理想 INL=0.00e+00`。
- `results/results.json` + `report.md` 可一键重算（约 6 s）。

### 3.3 模拟网表（B）

- 25 个块，每块 `spec.md + netlist/ sim/ reports/ layout/` 五件套。
- 28 个 .scs 参与编译（`analog/netlist/build.scs` 为编译根），220 实例 / 39 subckt，`check_hier.py` OK `[复核]`。
- `digital_stubs.scs` 的 `DigitalTop_stub` 与 SV 端口 **26 vs 26 逐字一致**，`check_ports.py` OK `[复核]`。
- **不能仿真**：`analog/netlist/pdk_models.scs` 只有填写说明，没有 include 任何工艺模型（D9）。

### 3.4 数字 RTL（C —— 骨架，功能不成立）

9 个模块：`DigitalTop / SliceSched / Sar1Ctrl / Sar2Ctrl / Sinc2 / ReconWeights / FramePack / SerLvds / tb_DigitalTop`，共 498 行。

**已完成的部分**：端口与模拟 stub 对齐；相位发生器计数正确；`SliceSched` 的 18 片轮换（base+8 mod 18，周期 9 次换相）逻辑成立；帧格式 24 bit 定义清晰。

**未成立的部分**：见 §4.1。最严重的一条是**整条链产不出有效码**：
> `Sar2Ctrl` 的 `done2` 永不置位 → `Sinc2` 收不到 8 个 valid → `acc_valid` 永不置位 → `ReconWeights` 不更新 → `DOUT` 恒为复位值 `0x200000`。（`[复核]` 静态推导，待仿真确认）

### 3.5 结论清单：能声称 / 不能声称（A，模型证据）

完整版 `TECH_EFFECTIVENESS.md`。摘要：

**能声称（有模型证据）**
1. DAC1 位权校准是 20 bit 的**必要条件**：不校准 SNDR 94.5 dB / SFDR 103.5 dBc，校准后回噪声底 **101.8 dB（+7.3 dB）**。
2. 级间增益校准第二重要：50 ppm 增益误差 = **−5.4 dB**（101.35 → 95.99）。
3. CAAZ 净收益 +3.62 dB，其中**独家只有 0.58 dB**，其余 3.04 dB 是任何两点平均都有。
4. 部分交织在 DR/SFDR 上是 **0.00 dB**，收益全在吞吐。
5. 洗牌：DR −1.0 dB 换 SFDR **+21.2 dBc**（103.7 → 124.9）。
6. 校准残差 ∝ 1/√n：n=1 → 2.3 ppm，n=256 → 0.14 ppm；判据 **≤1.5 ppm** 即可进噪声底 0.5 dB。

**只能声称方向**
- 8× tracking 的 +1.67 dB（区间 **+0.88 ~ +2.76**，取决于相关性机理；ρ=0.61 是反解值不是实测）。
- CAAZ 的 +3.62 dB（依赖未标定的 AZ 共享度）。
- 任何绝对 SNDR（模型缺参考建立/亚稳态/DAC 建立，实测必然更低）。

**不能声称**
- "校准后 INL = 0"（数学假象，实际是有限样本残差）。
- "交织提高 SNR"（本架构下不成立）。
- "SFDR 137 dBc"（模型无失真项，无物理意义；预期实测 100–110 dBc）。
- 任何面积/功耗之外的 signoff 级结论。

### 3.6 仓库与工程化（A）

- 远端 `git@github.com:defineiocc02/20bit10mSarAdc.git`，main。
- **本文件 r2 的提交 = `02f41f8`** `[复核]`；其前为 `a7584c6`（r1 交接文档）、`886e214`（图重做）、`cfb9bee`（模型口径修正）。要确认当前 HEAD 请用 `git -C /tmp/20bit10mSarAdc log -1`，不要信本文里的 hash。
- 每张图带 `manifest.json`（脚本 SHA256 / 数据 SHA256 / 输出 SHA256 / 字体 / 尺寸 / figure_count）。
- `CODE_INDEX.md` 索引全部代码入口；每个入口文件头有 `[CODE-INDEX]` 注释。

---

## 4. 待办事项

优先级定义：**P0 = 不做则后续全部无效**；P1 = 功能不对但可绕过；P2 = 欠账，不阻塞。

### 4.1 P0

| # | 事项 | 位置 | 动作 | 验收判据 |
|:--:|:---|:---|:---|:---|
| **D1** | `ReconWeights` 没有系数写入口，注释与实现不符 | `digital/ReconWeights.sv:1-6` vs `:21-27` | 加 `cfg_we/cfg_addr/cfg_data` 或直接上 SPI slave | 写 144 槽后读回全等；回灌后重构码与模型一致 |
| **D2** | 数字顶层没有校准/采集通路，`SerLvds` 从未例化 | `digital/DigitalTop.sv:15-47`（26 端口无 SPI/CAL_EN/CAL_DONE/TEST_MODE） | 补 SPI + 原始码导出 + `SerLvds` 例化 | 片外能读回原始码与 slice id；帧输出走 LVDS |
| **D3** | `Sar1Ctrl` 两个 `always_ff` 抢同一个 `idx` | `digital/Sar1Ctrl.sv:36-44` 与 `:49-61` | 合并成一个状态机，或用 `stage` 分支 | 综合无多驱动；仿真 idx 轨迹唯一 |
| **D4** | `Sar2Ctrl` 需要的 tick 数超过 ΦC2 窗口 | `digital/Sar2Ctrl.sv:25-44` vs `DigitalTop.sv:64` | 拉长 ΦC2（帧装不下）或把 8× 重复改并行/流水 | 一帧内 `done2` 能置位；`DT[7:0]` 全部有值 |

**D4 的精确账**（本轮静态数拍，修正 r1 的 19 拍）：
- SAR 阶段 `idx: 10→1` 共 **10 拍**（`d2[10:1]`，注意 `d2[0]` 全文件无赋值路径）；
- 重复阶段 `rep 0..6` 写 `dt[7:1]` **7 拍**，`rep==7` 写 `dt[0]` 并置 `done2` **1 拍**；
- 合计 **18 拍**（与 `CALIBRATION_GAP.md` §5 一致；r1 写 19 是把 `idx==0` 那拍重复计了一次）；
- 而 `PHI_C2 = cnt∈[10,17]` 只有 **8 拍**，且 `!phi_c2` 分支把 `idx` 复位成 10（`:41`）→ 永远走不到 `done2`。
- **衍生待确认**：若 11 bit 的 `d2[0]` 也要判决，则需 19 拍；但注释说 `DT[0]` 作 LSB 判决，两者哪个对，必须由数字侧按位账定死。

### 4.2 P1

| # | 事项 | 位置 | 动作 |
|:--:|:---|:---|:---|
| **D5** | `FramePack` 的 `count` 在同一 `always_ff` 里被 +1 和 −1 双写，后者覆盖前者 | `digital/FramePack.sv:33` / `:38` | 改 `nxt = count + wren - rden` 单次赋值 |
| **D6** | `Sinc2` 的累加结果被丢掉：`acc` 只接了 `acc_valid`，重构用原始 `D1/D2` | `digital/DigitalTop.sv:76-88` | 明确 8× 在模拟域还是数字域做，然后二选一改通 |
| **D7** | 系数个数口径未收敛 | 见 §5.3 | 先冻结 DAC1 物理结构，再定系数表 |
| **D8** | RTL 从未编译 | 全 `digital/` | 装 Icarus/Verilator（Windows 机已有 Icarus 12.0），9 个 .sv 编过再谈功能 |

### 4.3 P2

| # | 事项 | 说明 |
|:--:|:---|:---|
| **D9** | `analog/netlist/pdk_models.scs` 只有填写说明 | 不能跑 Spectre；文件内已写明不许用理想 MOS 代替（会把 L1 结论变假） |
| **D10** | 模型缺 5 类非理想 | 参考纹波/建立、比较器亚稳态、DAC 建立、开关电荷注入、采样网络带宽。已有：kT/C、RA 宽带、RA AZ、比较器、基准噪声、DAC1 静态 INL、在环 ADC2 量化、时钟抖动（默认 0） |
| **D11** | 16.4 ppm 依赖"同一阵列互补开关"假设 | 若 P/N 是独立阵列，量级回到 ~23 ppm（`REFERENCE_AUDIT.md` §1-4）。引用必须带前提 |
| **D12** | 洗牌在 RTL 里做不了 | `SliceSched.sv` 只输出 18 bit 掩码 + base，没有**有序** 5 bit slice id → 重建不知道用了哪 8 片、什么顺序。模型里"洗牌 +21 dBc"目前无 RTL 支撑 |
| **D13** | 面积没经过任何版图验证 | core 0.70–1.0 mm² 是自底向上算的；对标 CICC 0.53 mm² 反推 MIM 密度 2 fF/µm² |
| **D14** | `tb_DigitalTop` 语义错 | 每帧只给 1 个 `DONE2`，而 `Sinc2` 需要 8 个 valid 才输出 → 帧率变成 fs/8；且 `initial` 里用了非阻塞赋值 `[复核]` |
| **D15** | 本地无版本控制 | `20b10m/` 在外层仓库中是未跟踪目录（`?? pipelinedsar工作站/20b10m/`）`[复核]`；改动前请先 commit/push，否则无回滚点 |

---

## 5. 已知问题与风险

### 5.1 缺陷清单

见 §4 的 D1–D15（按优先级分组，已含位置与验收判据）。**本轮新增的 3 条**：D4 的精确拍数（18 非 19）、`d2[0]` 无赋值路径、D14/D15。

### 5.2 风险登记

**技术风险（`PLAN.md` §8，未变）**

| # | 风险 | 触发 | 缓解 | 责任域 |
|:--|:---|:---|:---|:---|
| R1 | 18:1 SliceMux 偏斜/电荷注入 | 片间 >50 ps | 对称树、等长、dummy、先断后合 | 版图 + 模拟 |
| R2 | 参考 droop/回流 | 比较时刻 >2.44 mV | 1 nF 片上 + 封装 1 µF + R_buf ≤20 Ω | 模拟 |
| R3 | PDK MIM 密度只有 1 fF/µm² | core >0.8 mm² | 2 fF/µm² 堆叠 / 4+2 粗量化 / 去耦 150 pF | 版图 + 架构 |
| R4 | 2 MHz 抖动 | σt >1 ps | 外部时钟、独立 LDO/pad、0.5 ps 目标 | 架构 + 数字 |
| R5 | 数字/模拟耦合 | 固定码 INL 变 >0.5 LSB | 分区、guard ring、独立电源、末次翻转 ≥8 ns | 版图 |
| R6 | C_INC + replica 匹配不好 | 版图不对称 / 时序不齐 | 版图阶段前先做匹配敏感性仿真 | 模拟 |
| R7 | 28 pF DAC1 在 90 ns 内建立不足 | 驱动不够 / 三电平规划不当 | G1 就把握建立预算写进时序表 | 架构 + 模拟 |

**工程风险（本轮补充）**

| # | 风险 | 触发 | 后果 |
|:--|:---|:---|:---|
| R8 | 数字链"看起来有 RTL" | 只看文件清单 | 误以为 G2 已完成；实际编不过、跑不出码 |
| R9 | 文档口径分叉 | 同时读 `STATUS.md` / `PLAN.md` / `HANDOVER.md` | 下一步完全不同（见 §5.3） |
| R10 | 改模型参数不溯源 | 把 ρ=0.61 当实测 | tracking 收益被高估，区间外推失效 |
| R11 | 无仿真工具下改 RTL | 本机无 iverilog | 改完无法验证，越改越不确定 |

### 5.3 文档冲突与失效声明（接手必看）

| 文档 | 声称 | 实际 | 处置 |
|:---|:---|:---|:---|
| `STATUS.md`（根目录） | "G0 进行中，8 个待定参数未定" | 项目已到 G1 收尾 | **已过时**，只作历史记录；本版已加顶部声明 |
| `PLAN.md` §9 | "55 张图"、"下一步填 pdk_models" | 实际 75 PNG；下一步是 M0/M1 | 部分过时，里程碑以本文 §7 为准 |
| `HANDOVER.md` r1 | "远端最新 886e214" | 实际 `a7584c6` `[复核]` | 本版已更正 |
| `digital/README.md:46` | "48 个系数" | 实现里 0 个；`CALIBRATION_GAP` 要求 144 | 待 M0 冻结 |
| `interface/OUTPUT_IF_10M.md:91` | 40 槽 × 24 bit | 需求 144（或 34，取决于结构） | 待 M0 冻结 |
| `plan/phase2_digital.md:702` | 28 + 18 + 2 ≈ 48，寄存器留 64×22 | 同上 | 待 M0 冻结 |
| `digital/CALIBRATION_GAP.md` §2.2 | 126 + 18 = **144** | 按 18 片池口径成立；若单一阵列则是 **34** | 取决于 DAC1 物理结构 |
| `PLAN.md` G3 判据 | SNDR ≥97 @100k | `STATUS.md`/`README` 目标 99.4 | 目标与门禁判据不同，别混用 |

---

## 6. 相关文件与代码位置

### 6.1 目录地图

```
20b10m/                         35 MB，464 文件
├── README.md                   工程总览（112 行）
├── HANDOVER.md                 本文件（唯一入口）
├── TECH_EFFECTIVENESS.md    ★  各技术有效性对比（结论总表，152 行）
├── PLAN.md                     WBS / 门禁 G0–G6 / 排期（§9 部分过时）
├── CODE_INDEX.md               代码索引（带行数）
├── FILE_LAYOUT.md              文件存放规范
├── plan/                       14 份：架构裁决、粗量化、面积模型、面积对标、floorplan、走线
├── spec/                       6 份：规格树、位分配、时序（interfaces.csv 为端口唯一权威）
├── interface/                  16 份：引脚 48/32、输出协议、时序图（含 4 PNG）
├── analog/
│   ├── blocks/                 25 个块，每块 spec.md + netlist/ sim/ reports/ layout/
│   ├── netlist/                28 个 .scs（build.scs 是编译根）、check_hier.py、check_ports.py
│   ├── area_model.md           自底向上面积
│   ├── area_vs_cicc.md         与 CICC 0.53 mm² 对标（反推 MIM 2 fF/µm²）
│   ├── floorplan_4mm.md        部分交织版图布局 + PNG
│   └── routing_plan.md         从 CICC die photo 识别的走线规则
├── digital/
│   ├── *.sv                    9 个模块 + tb（498 行，未编译）
│   ├── CALIBRATION_GAP.md   ★  校准链路缺口（427 行，带 file:line）
│   └── README.md               数字侧说明（注意 :46 的 48 系数说法与实现不符）
├── model/
│   ├── *.py                    14 个文件 2106 行
│   ├── REFERENCE_AUDIT.md   ★  与参考实现逐点对照（274 行）
│   ├── AUDIT.md                早期可信度说明
│   ├── PLOT_DESIGN.md          出图规范
│   └── results/                results.json / report.md / figures{,_paper,_measured,_plots}/ + manifest
├── verilog/                    端口桩
├── review/20261107_self_audit.md  自查报告（9 项）
└── docs/ skill/                导入步骤、建库脚本
```

带 ★ 的三份是本轮核心产出，其余是支撑材料。

### 6.2 关键 file:line 索引

| 要找什么 | 位置 |
|:---|:---|
| 全部结论与 ΔSNDR 排名 | `TECH_EFFECTIVENESS.md` §1 |
| 能声称/不能声称（模型口径） | `TECH_EFFECTIVENESS.md` §4、`model/REFERENCE_AUDIT.md` §3 |
| 校准链路缺口（含改动方案） | `digital/CALIBRATION_GAP.md` §3（必修/建议/可延后）、§4（方案，未改文件） |
| 系数表建议与槽位核算 | `CALIBRATION_GAP.md` §2.2、§4.1（144+16=160 槽） |
| 相位发生器与帧时序 | `digital/DigitalTop.sv:57-68` |
| 数字端口（26 个） | `digital/DigitalTop.sv:16-47`；对照 `analog/netlist/digital_stubs.scs` |
| 位重组与系数（缺入口） | `digital/ReconWeights.sv:1-27` |
| 一级 SAR 双驱动 | `digital/Sar1Ctrl.sv:36-44`、`:49-61` |
| 二级 SAR 拍数不足 | `digital/Sar2Ctrl.sv:25-44` |
| 8× 重复累加（结果被丢） | `digital/Sinc2.sv`；`DigitalTop.sv:76-88` |
| 帧 FIFO 计数双写 | `digital/FramePack.sv:33`、`:38` |
| 18 片调度（无有序 id） | `digital/SliceSched.sv:16-22`、`:33-40` |
| 冻结参数（噪声/ρ/交织） | `model/params.py`（头部注明哪些是实测、哪些是反解） |
| 静态 INL 两套拓扑 | `model/static.py:curves()` vs `curves_binary()` |
| 图清单与 SHA256 | `model/results/figures*/manifest.json` |
| 端口唯一权威 | `spec/interfaces.csv` |
| PDK 待填 | `analog/netlist/pdk_models.scs` |

### 6.3 命令手册

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
python3 analog/netlist/check_hier.py    # 层次/实例数 → files=28 subckts=39 instances=220
python3 analog/netlist/check_ports.py   # 数字↔模拟端口 → 26 vs 26 OK

# 推送（SSH 通道，已配好）
rsync -a --delete --exclude='.git' ./ /tmp/20bit10mSarAdc/20b10m/
cd /tmp/20bit10mSarAdc && git add -A && git commit -m "..." && git push origin main
```

⚠️ `/tmp/20bit10mSarAdc` 是临时克隆，随时可能被清掉；丢了重新 `git clone git@github.com:defineiocc02/20bit10mSarAdc.git`，仓库里已有完整内容（本文件 r2 自 `02f41f8` 起）。
⚠️ 本机 Python 3.13.12（`~/.workbuddy/binaries/python/versions/3.13.12/bin/python3`），numpy 2.5.4 / matplotlib 3.11.2。**本机无 iverilog / verilator / yosys**；Spectre / Calibre / Virtuoso 在另一套环境。

### 6.4 模型口径与踩过的坑（别再踩一遍）

1. **矩形窗必须严格相干。** `metrics.fft_metrics` 有硬断言：fin 偏 0.25 bin 时 SNDR 会从 102 dB 掉到 **13.8 dB**，而且不报错。所有实验先 `round(fin*N/fs)*fs/N`。
2. **DNL 必须用同一条拟合直线的斜率归一。** 用标称 LSB1 会产生 `mean(DNL)=+2.23 ppm` 的不自洽。
3. **校准残差不是 0。** 理想 0 只在"INL 恰由位权误差张成 + 权重无限准"时成立。用 `cal_residual(n_avg)`（∝1/√n）。任何"校准后 INL=0"的图都是错的。
4. **静态模型有两套拓扑，别混用。** `static.curves()` 默认本项目拓扑（8 unary × 128，INL 16.4 ppm）；`curves_binary()` 是旧的单端 10 bit 二进制（38.6 ppm），差 2.3 倍。
5. **AR(1) 沿"重复次数 m"递推是假设，不是参考实现做法。** 参考里没有 M 次平均机制。引用 +1.67 dB 必须带区间。
6. **字体**：`font.family` 必须是列表 `["Hiragino Sans GB","Arial","DejaVu Sans"]`，否则 µ 和 − 变方框；mathtext 解析不到列表，对数轴统一用 `viz._plain_log_axes`。
7. **标题定位用毫米不用百分比**（`viz.annotate`）：74 mm 高的图上百分比定位会让标题压住副标题。
8. **`model/plots.py` 曾写进 `results/figures/`，把 41 图 manifest 覆盖成 5 条**（已改成写 `figures_plots/`）。若 `figures/manifest.json` 的 `figure_count` 不是 41，重跑 `python3 -m model.figures` 恢复。
9. **出图必须用 ViewImage 真看。** 只看 "wrote N figures" 会漏掉标题被裁、文字压曲线、刻度 `1e+02` 偏移——上一轮就漏过三次。

---

## 7. 下一步建议

### 7.1 里程碑（按依赖排序）

| 里程碑 | 内容 | 验收标准 | 依赖 |
|:---|:---|:---|:---|
| **M0** | 冻结 DAC1 物理结构（单一 1023+16 阵列 vs 18 片独立池），同步 40/48/64/144/34 五个口径 | 三份 plan 说法一致；系数表冻结（每项：名字/位宽/Q 格式/名义值/训练上界） | 架构评审，1 次会 |
| **M1** | 修 D3/D4/D5/D6/D14，装 Icarus 或 Verilator，9 个 .sv 编过 + `tb_DigitalTop` 跑通 | `iverilog -g2012` 零 warning；tb 输出 1 帧正确数据 | M0（D4 的时序改法依赖位账） |
| **M2** | 加 SPI 系数写入口 + 校准采集模式（原始码 + 有序 slice id） | 片外能读回 144 组码、能回灌权重；回灌后重构码与模型一致 | M1 |
| **M3** | 填 `pdk_models.scs`，网表跑通 DC/AC/瞬态（每块一个 testbench） | 25 个块至少 top + DAC1 + RA + CT2 有仿真结果 | PDK 环境 |
| **M4** | 补模型缺的 5 类非理想（D10），重跑全部图 | 图注里的"未建模"逐条销账 | 可与 M1–M3 并行 |

### 7.2 两条线怎么并行

- **数字线（M0→M1→M2）**：唯一的硬依赖是 M0。M0 一冻结，D3/D5/D6/D14 可以立刻改（不依赖系数个数），D4 的改法才需要位账。
- **模拟线（M3）**：不依赖 M0，只依赖 PDK 环境。填 `pdk_models.scs` + 关键块 testbench 可以马上开始。
- **模型线（M4）**：完全独立，随时可做，且能反过来给 M0 提供判据（例如参考建立要多少 ns 才不掉 SNDR）。

### 7.3 不建议现在做的

**版图。** 面积还没被任何仿真校准过（RA 噪声、DAC1 单位电容、参考 buffer 驱动能力全是预算值），先做版图会返工。等 M3 有前仿结果、M0 冻结结构后再开 G4。

---

## 8. 接手检查表

**第一小时**
- [ ] `cd 20b10m && python3 -m model.selftest` → 4 项 PASS（本轮实测通过）
- [ ] 读 `TECH_EFFECTIVENESS.md`（152 行）——这是全部结论
- [ ] 读 §4.1 的 P0 四条，确认你认同优先级
- [ ] `git -C /tmp/20bit10mSarAdc log --oneline -5` 确认远端可用；`02f41f8` 及之后应能看到本文件；若临时克隆没了，先 clone

**第一天**
- [ ] 随机抽 3 张图用看图工具打开，对照 `manifest.json` 的 SHA256（确认图不是旧的）
- [ ] 读 `model/REFERENCE_AUDIT.md` §3「能声称/不能声称」，与 `TECH_EFFECTIVENESS.md` §4 对一遍
- [ ] 打开 `digital/Sar1Ctrl.sv`，自己确认 `idx` 是不是真被两个 always 驱动（别信文档，信代码）
- [ ] 打开 `digital/Sar2Ctrl.sv`，自己数一遍拍数，并确认 `d2[0]` 有没有赋值路径
- [ ] 决定 M0 的会什么时候开

**第一个坑预警**
- [ ] 改模型参数前先看 `model/params.py` 头部注释（哪些是实测、哪些是反解推断）。**ρ=0.61 是反解值，不是实测。**
- [ ] 改 RTL 前先确认有没有仿真工具，否则改完也不知道对不对。
- [ ] 改任何东西前先 `git commit` 到远端——本地目录不受版本控制（D15）。

---

## 9. 本版整理说明（r1 → r2）

**做了什么**：按"接手者视角"重组为 目标 / 进展 / 已完成 / 待办 / 问题与风险 / 文件位置 / 下一步，并逐条复核了 r1 中的可验证断言。

**本轮实际执行的校验**（L0 静态 + L1 运行）：
1. `python3 -m model.selftest` → 4/4 PASS。
2. `python3 analog/netlist/check_hier.py` → `files=28 subckts=39 instances=220`，OK。
3. `python3 analog/netlist/check_ports.py` → `26 vs 26`，OK。
4. 图清单：`figure_count` 41 / 14 / 9；PNG 合计 75（含 5 旧格式 + 6 版图/引脚）。
5. `model/*.py` → 14 文件 2106 行（r1 写 2105）。
6. RTL 逐点复核：D1/D2/D3/D5/D6/D12 全部属实，行号未漂移。
7. `git log` → 远端 HEAD `a7584c6`（r1 写 `886e214`）。
8. 外层仓库 `git ls-files 20b10m` → 0，确认本地不受版本控制。

**本版修正/新增的事实**
- D4 拍数由 **19** 更正为 **18**（10 拍 SAR + 8 拍重复；r1 把 `idx==0` 那拍重复计了一次），并补上"若 `d2[0]` 也要判决则 19 拍"的分支。
- 新增：`Sar2Ctrl` 中 `d2[0]` 无任何赋值路径（11 bit 只落了 10 bit），需数字侧按位账确认。
- 新增：按现状 `done2` 永不置位 → `acc_valid` 永不置位 → `DOUT` 恒为 `0x200000`，**整条数字链不产出有效码**。
- 新增 D14：`tb_DigitalTop` 每帧只给 1 个 `DONE2`，Sinc2 需 8 个才输出，帧率变 fs/8。
- 新增 D15：本地 `20b10m/` 未被任何仓库跟踪。
- 新增 §5.3 文档冲突表（`STATUS.md` 过时、`PLAN.md` §9 过时、系数 40/48/64/144/34 五套口径）。
- 补 §2.4 G0–G6 门禁映射，直接回答"项目到底到哪了"。

**未做的事**：没有改动任何 RTL、模型参数或网表；没有重跑 `experiments`/`figures`（图与 `results.json` 保持 r1 状态）；RTL 的功能判断仍全部是文本级静态复核，**没有编译、没有仿真**。

**回滚**：原文件备份在 `/tmp/HANDOVER_r1_20261108.bak`；仓库内 r1 版本为 `git a7584c6`（`git show a7584c6:HANDOVER.md`）。
