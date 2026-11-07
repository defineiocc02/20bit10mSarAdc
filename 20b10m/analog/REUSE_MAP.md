# Pipe_SAR 复用矩阵（10 MS/s 项目，2026-11-07）

> 源库：`Pipe_SAR/`（65 nm LP，1.2 V，6b+8b 两级，~100 MS/s，OA 库，无 layout/无网表）。
> 结论：**可复用顺序是"拓扑 > 单元 > 方法学"，不是"整块搬"。** 能直接搬的只有小开关/比较器/逻辑门；DAC、RA、参考必须按 180 nm BCD 5 V 重画。
> 复用等级：**R0** 原样复用（symbol 不改，仅改尺寸参数）｜**R1** 拓扑复用，重画尺寸/耐压｜**R2** 仅测试台/方法学复用｜**R3** 不可用。

## 1. 逐单元映射

| Pipe_SAR 单元 | 角色 | 我们的落点 | 等级 | 必须改什么 | 风险 |
|:---|:---|:---|:---:|:---|:---|
| `Bootstrap` | 自举采样开关（基型） | `SwSample5v` | **R1** | 1.2 V→5 V 厚栅；C_boot 0.45→1.7 pF；Ron 线性度按 20 bit 重算；加 hold-high 钳位 | 栅压过应力、体效应 |
| `Bootstrap2` | 自举变体 | `SwSample5v` 备选 | R1 | 同上；用于对比 Ron 线性度 | 同上 |
| `SW2-1s` | 采样 2:1（VIN/VCM） | `SwSample5v` 内部 | R1 | 5 V TG，VCM=2.5 V | 电荷注入 |
| `TG` / `TG1` / `TG_2C/4C/8C` | 传输门（多尺寸） | `RaMux`、`TriLevelDrv`、DAC 底板开关 | **R0/R1** | 尺寸按 5 V 耐压重选；TG_8C 可用于 RaMux 主通路 | 5 V 下 Ron 非线性 |
| `DYSARcontrl` | 每位三电平 DAC 开关驱动 | `TriLevelDrv` | **R1** | 三轨 VREF/VCM/VGND=5/2.5/0 V；驱动 74 µm 栅宽；加死区 | 三轨串通、直通电流 |
| `DYSARlogic` | 异步 SAR 逐次逼近 | `SarLogic1` / `SarLogic2` | **R1** | 11 位；ready 驱动自定时；包络截断；M=8 计数器 | 自定时在 ss 角丢位 |
| `comparator4in2` | 四输入动态比较器 | `Cmp1`、`CmpCoarse6b`（×63） | **R1** | 输入对改 5 V 厚栅；噪声按 366 µV@顶板；失调修调（63 个） | 5 V 输入对面积/DNW |
| `comparator_pin` | 二级比较器 | `Cmp2` | **R1** | 1.8 V 域；2.36 ns/bit；噪声 ≤11.4 µV 折输入 | 亚稳态 |
| `D_adjust2` | 数字冗余重组 6+8→12 | `BitRecombine` | **R2** | 位宽改 10+11→22；只借"先加冗余再截断"的结构 | 位宽错一位全错 |
| `Dflip-flop` + 缺失 `NOT_delay` | 数字单元 | 数字标准单元 | R2 | 不搬，用 180 nm 标准单元库；`NOT_delay` 自己写 3 bit 可调 | — |
| `1b_adder` / `And` / `Or` / `XOR` / `OAND` / `OOR` | 逻辑门 | 数字综合 | R2 | 不搬 | — |
| `ampGA` / `ampGB` / `amp_gainboost` | 两级 gain-boost 余差放大器 | `RingAmp3` 的**拓扑参考** | **R1** | 1.2 V→1.8 V；换成三级 ring amp（A1 FIA/A2/A3）；4 pF 负载；1.7 V 摆幅；AZ | 直接搬会摆幅/噪声都不够 |
| `Bias` | 偏置/带隙（引用缺失 `bandgap`） | `BiasGen` | R1 | 5 V/1.8 V 双域偏置；bandgap 需自建或外供 | `bandgap` 缺失 |
| `DAC_VA` / `DAC_VA12` / `DAC_7bit_0.4ref` | 理想行为级 DAC | **仅测试台** | **R2** | 保留为 `tb/` 里的理想参考，**不得进硅片网表** | 行为级当电路结论 |
| `Difference1` | 理想减法器 | 测试台误差观测 | R2 | 保留 | — |
| `Pi-SAR_amp` | 顶层 testbench | `tb/Sar20bTop_tb.scs` 结构参考 | R2 | 换成 10 MS/s 两相 | — |
| `DYSAR6b_200M` | 独立 6b SAR | 6b flash 的**时序参考** | R2 | 我们是 63 cmp flash，不是 6 拍 SAR | 结构不同 |
| `PiSAR_2st_8bit` | 两级 ADC 主体 | — | **R3** | 6+8 位、65 nm、无 CT 二级，与目标不符 | 不可作基础 |

## 2. 能直接拿的三样东西（优先级最高）

1. **`comparator4in2` 的版图/尺寸**：四输入结构天然适合"信号对 + 参考对"，63 个粗量化器可直接实例化同一单元，修调只加在参考侧。
2. **`DYSARcontrl` 的三电平驱动时序**：它已经处理了"每位三轨切换 + 死区"，我们只需把轨电压从 1.2/0.6/0 改成 5/2.5/0，并把驱动能力按 74 µm 栅宽放大。
3. **`DYSARlogic` 的异步握手骨架**：ready/valid 的位循环可以直接改成 11 位 + 包络截断；`NOT_delay` 用 3 bit 可调延迟线替代（原库缺失）。

## 3. 绝对不能拿的三样

| 项 | 原因 |
|:---|:---|
| `amp_gainboost` 直接做 RA | 65 nm 1.2 V，输出摆幅 <1.2 V；我们需要 1.7 V + 三级 + AZ，结构不同 |
| 理想 DAC 模型当电路 | `DAC_VA*` 是 Verilog-A，没有失配/寄生/kickback；用它验 20 bit 必然假通过 |
| 65 nm 的 MOM 单位电容 | 19.7 fF vs 我们 27 fF；密度、匹配常数、电压系数全不同 |

## 4. 复用工作的落地顺序

1. **先把 `Bootstrap`/`comparator4in2`/`DYSARcontrl` 三个单元在 180 nm 下重画并单独仿真**（L1），判据见各块 `spec.md`；这三个过了，60% 的模拟风险就落地了。
2. **再做 `SdacSlice`（128 单位 + 7 bit）**：它是 18 片池的基本单元，先做单片后做池。
3. **最后做 `RingAmp3` 与 `RefBuffer`**：这两个是全新设计，Pipe_SAR 只提供"两级放大 + 偏置"的版图习惯，不提供可复用电路。
