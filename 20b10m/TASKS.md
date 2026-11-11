# 任务与验收追踪表（BL-v3 口径）

> 唯一任务入口。旧表（ARCH_V2 的 10+11+1.5−2 口径）已归档到 `spec/TASKS_ARCH_V2_legacy.md`。
> 状态两轴：**设计**（候选/采用/弃用）× **实现**（未开始/进行中/可运行/已验证/受阻）。
> 证据：文档 / 静态检查 / Python / RTL / 晶体管 / AMS / 后端 / 硅测 —— **不可互替**。

---

## A. 阻断级（P0）

### T-A01 参考 buffer 输出阻抗 ≤0.67 Ω

| 项 | 内容 |
|:---|:---|
| 工作域 | 模拟 |
| 问题 | droop 在比较时刻的残余必须 <0.1 LSB1。由恒等式 `残余/峰值 = exp(−t/(R·C))`，**唯一约束是 R** |
| 输入 | `spec/DROOP_OPTIONS.md` v3；C_decap=300 pF、t_cmp=1 ns、Q=69.1 pC/次 × 4 次/样本 |
| 前置 | 无 |
| 责任 | 模拟；协作：架构（指标）、版图（去耦与地） |
| 文件 | `analog/blocks/RefBuffer/netlist/RefBuffer.scs`（重写） |
| 交付 | ① 拓扑：**两级**——1.8 V 折叠 cascode 误差放大器 + 5 V 推挽输出级（0.67 Ω 需 gm ≥1.5 S，5 V 器件 fT 不够，必须分开）；② CDL；③ 前仿 Zout(f)、阶跃恢复、PSRR、噪声 |
| 验收 | 小信号 Zout ≤0.67 Ω（1 kHz–10 MHz）；69 pC/0.3 ns 阶跃恢复 <1 ns；平均电流 ≤3.5 mA；输出噪声 ≤2.9 µV（折输入）；**L1** |
| 状态 | 设计：采用；实现：**未开始**（现网表调整管无上拉，拓扑错） |
| 阻塞 | PDK（无 5 V 器件模型） |
| 风险 | 0.67 Ω 是**小信号**指标；大信号由 C_decap 承担，但输出级不能进压摆限 |

### T-A02 Cmp2 收紧到 ≤1.05 ns（SS）

| 项 | 内容 |
|:---|:---|
| 问题 | ΦC2 45 ns / 20 拍 = 2.25 ns；SS 下 1.2+0.3+0.9 = 2.40，超 0.15 |
| 文件 | `analog/blocks/Cmp2/netlist/Cmp2.scs` |
| 交付 | tail 12 → ≥18 µA；CDL + 延迟前仿（TT/SS/−40/125 ℃） |
| 验收 | TT ≤0.9 ns、SS ≤1.05 ns；失调 ≤1 LSB2；噪声 ≤50 µV；**L1** |
| 代价 | +0.2 mW |
| 状态 | 未开始 |

---

## B. 设计前必须闭合（P1）

| ID | 任务 | 交付 | 验收 | 状态 |
|:---|:---|:---|:---|:---|
| T-B01 | **DAC2 12 bit 分段** | 6+6 与 7+5 的 C_top/α/桥容/kickback 对比，选一 | C_top ≤1.8 pF；1 LSB2_DAC ≤0.5 LSB2 | 未开始 |
| T-B02 | 冗余 2 bit vs 1 bit | DAC1 最坏误差（0.65 LSB1 校准 + 0.007 建立 + 失调）vs 窗口余量表 | 结论 + 理由 | 未开始 |
| T-B03 | **DAC1 网表 7 bit → 10 bit** | 每片独立 7 bit + 3 bit 片选；CDL | 1024 码逐码扫，LSB 台阶 = 1 单位；**L2** | 未开始 |
| T-B04 | 三电平接线 | VREF/VCM/VGND 三档译码接底板 | MSB 电荷减半（69→34.6 pC） | 未开始（可选） |
| T-B05 | 四个缺失块 | `CapTrim`/`ClkRx`/`PhiGen`/`PhaseSplit` 的 spec + CDL | A/B skew ≤1.6 ps；CapTrim 行程 ≥40 ps | 未开始 |

---

## C. 数字侧

| ID | 任务 | 文件 | 验收 | 状态 |
|:---|:---|:---|:---|:---|
| T-C01 | 相位 10/15/20/45 | `digital/DigitalTop.sv` | 波形不重叠；AZ 早关 RA ≥2 ns | 可运行（口径旧） |
| T-C02 | `NB_D2` 11→12 | `digital/Sar2Ctrl.sv` | 20 轮全落位；done2 每帧 1 次 | 可运行 |
| T-C03 | `Sinc2` 三处 | `digital/Sinc2.sv` | `sum` 每帧清零；`dt` 参与；出帧率 = fs | 有缺陷 |
| T-C04 | `ReconWeights` 权重 | `digital/ReconWeights.sv` | 逐码 bit-exact（Python 定点 vs RTL） | 权重错 |
| T-C05 | `SliceSched` 固定模式 | `digital/SliceSched.sv` | 16 片两两交替、2 片备用、stall 正确 | 有 Python 参考 |
| T-C06 | `SerLvds` 例化 | `digital/DigitalTop.sv` | 400 Mbit/s 波形 | 未例化 |

**全部零编译**（本机无 iverilog/verilator）→ 状态一律 `NOT_RUN`。

---

## D. 接口与物理

| ID | 任务 | 交付 | 状态 |
|:---|:---|:---|:---|
| T-D01 | 引脚表 | `interface/PINOUT.md`（48 版 + 最少工作集） | 本轮已建，待确认封装 |
| T-D02 | 输出协议 | 22 bit 帧格式、线速、lane、对齐 | 待确认 |
| T-D03 | **一致性脚本** | `tools/check_consistency.py` + 正反例 | **本轮已建** |

---

## E. 验证

| ID | 任务 | 验收 | 状态 |
|:---|:---|:---|:---|
| T-E01 | 网表 L1 前仿 | 每块 vs spec 判据 | 阻塞（PDK） |
| T-E02 | 系统 L2（Python） | DROOP/INL/SNDR | 部分完成 |
| T-E03 | MC/PVT | 校准后残差 ≤2 LSB | 未开始 |
| T-E04 | DRC/LVS | 零错 | 未开始 |

---

## F. 已完成并有证据

| 项 | 证据 | 层级 |
|:---|:---|:---|
| 位账自洽 20.0 bit | `behavioral` 断言 | Python 断言 |
| 码域闭合 σu=0 → INL 0.000 LSB20 | `runs/smoke_ramp` | Python 实跑 |
| 理想链 SNDR 122.06 dB / ENOB 19.98 | `runs/smoke_tone` | Python 实跑 |
| 失配→INL 线性（0.02%→4.6、0.2%→45.3 LSB） | 同上 | Python 实跑 |
| 校准 27× | 同上 | Python 实跑 |
| 8× 收益 +1.86 dB | `review/20261108_round2_digital.md` | Python 实跑 |
| 网表层次 28 文件/220 实例/端口一致 | `check_hier.py` | 静态检查 |
| droop 只需 R ≤0.67 Ω | `spec/DROOP_OPTIONS.md` v3 | 推导 |

**这些都不代表芯片可用**：零晶体管仿真、零 RTL 编译、零版图。
