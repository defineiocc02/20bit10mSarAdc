# 20bit10mSarAdc 工程评审：CDAC 结构、数字接口、DEM/dither 与可复现性

> 评审对象：`github.com/defineiocc02/20bit10mSarAdc`（main `02e5b26`，2026-11-08）
> 对照物：本机同源工作副本 `20b10m/`（比远端多 100 个文件，含 `STATE.md`/`TASKS.md`/`analog/BLOCK_CONTRACTS.md`/`behavioral/`/`arch/`）
> 方法：逐行读网表与 RTL、跑仓库自带检查与行为模型、对回公开论文与专利权利要求
> 证据分级：L0 静态结构 / L1 行为模型 / L2 前仿 / L3 后仿 / L4 PVT / L5 硅测。本文所有结论最高到 **L1**。

---

## 0. 五条结论（先看这个）

1. **树不是"乱"，是"三层口径同时活着"**：论文口径（20.5 bit / 11+12−2.5 / G=128）、README 口径（20.5 / 10+11+1.5−2 / 28 pF）、BL-v3 口径（20.0 / 10+12−2 / 10 Vpp）三套并存；模拟网表、数字 RTL、接口文档各认一套。这不是排版问题，是**同一个信号有三套位宽**。
2. **模拟 CDAC 的网表结构 ≠ 文档写的结构**。网表里 DAC1 是 **8 片 ×128 单位（27 fF）的 7 bit 二进制 CDAC，底板两电平（VREFP/VREFN）**；文档写的"片间 3 bit unary + 片内 7 bit = 10 bit"和"三电平（VREF/VCM/VGND）"**在网表里都没有落点**（`SdacPool18.scs:15-49` 18 片共用同一 `D<6:0>`；`Sar20bTop.scs:24` 只接 `D1<6:0>`，高 4 位被丢；`TriLevelDrv` 输出 `SEG<10:0>` 悬空）。
3. **DAC2 是唯一画对了的 CDAC**：5 bit 主阵（32×27 fF）+ 串联桥 28 fF + 6 bit 子阵（64×27 fF），顶板 ≈0.89 pF；桥容 28 fF 对应 β≈1/62.7，比理想 1/64 偏 +2.1%（安全侧），不是"错 2×"。但它 **11 bit，不是 12 bit**，且 12 个复位 TG 的 `RST` 端口不存在（`Dac2_11b.scs:55-65` 悬空）。
4. **数字侧现在拿不到能开工的接口**：缺 `CMP1/2_READY` 握手、缺 `D1_MASK` 位序与位宽、缺每片权重表、缺 dither 的码域定义与扣除公式、缺校准可观测量。接口文档 `ANALOG_DIGITAL_IF.md` 还是 v0.9-draft，7 项未签。
5. **DEM 在本仓库不存在；dither 只有"字生成"，没有注入通路**。行为模型没有 DEM/dither 维度（`model/*.py` 零命中）；数字 RTL 也没有（`digital/*.sv` 零命中）。能跑的"shuffle"是**切片级 8/18 随机选择**，实测 DR −1.0 dB / SFDR +21.2 dBc，**不能当 DEM 收益引用**。DEM/dither 也不属于 AD4080 的输出 DSP（`ad4080_dsp/` 只有 SINC、sys_error_corr、FIFO、SPI、GPIO）——它们属于 ADC 核内的 DAC 开关驱动。

---

## 1. 工程树体检：乱在哪，量化

### 1.1 规模与构成

| 项 | 远端 | 本机工作副本 | 说明 |
|:---|:---:|:---:|:---|
| 文件总数 | 373 | 473 | 远端缺 100 个 |
| `.md` | 86 | 117 | 文档比代码多 |
| `.png` / `.svg` / `.pdf` | 75 / 69 / 69 | 81 / 71 / 69 | 69 个 PDF **全是模型出图**，不是论文/数据手册 |
| `.py` | 22 | 56 | 远端缺 `digital_tech.py`/`impairments.py`/`simulate_v2.py`/`plots_compare.py`/整个 `arch/` `behavioral/` |
| `.sv` | 9 | 9 | 合计 498 行，最大的 `DigitalTop.sv` 102 行 |
| `.scs` | 32 | 32 | 23 个块，**693 行**，全是理想电容 + 理想开关 |

结论：这是一个**文档/图为主的计划仓库**，不是可仿真工程。按"代码行/文档行"算，模拟网表 693 行、数字 RTL 498 行、文档 100+ 篇。

### 1.2 六套"唯一真相"并存

| 文件 | 自称 | 实际冲突 |
|:---|:---|:---|
| `README.md` | 20.5 bit / 10+11+1.5−2 / 28 pF / ΦC0 7.5-15-25-37.5 | 与 BL-v3、接口文档都不同 |
| `HANDOVER.md` | 交接真相 | 与 `STATE.md`/`TASKS.md` 内容重叠 |
| `STATE.md`、`TASKS.md` | 状态/任务 | 只在本地，未推远端 |
| `spec/ARCH_DECISION_BLv3.md` | "唯一权威" | **只在本地，远端没有**；且改成了 20.0 bit |
| `spec/ARCH_V2.md` + `README_ARCH_V2_legacy.md` | 旧权威 | 与 BL-v3 并存 |
| `spec/bit_allocation.md` | 位分配 | BL-v3 明文"全文取代" |

任何人都能引一份"权威"文档得出不同位账。这是"乱"的第一因。

### 1.3 位账三套（可逐项复算）

| 口径 | 公式 | 值 | LSB2/总 LSB | 出处 |
|:---|:---|:---:|:---:|:---|
| 论文 | 11 + 12 − 2.5 | 20.5 | 1.0 | `bit_allocation.md` 引论文 p.36 |
| README | 10 + 11 + 1.5(8×) − 2 | 20.5 | 2^1.5 | `README.md` §1 |
| BL-v3 | 10 + 12 − 2 | 20.0 | 1.0 | `spec/ARCH_DECISION_BLv3.md` §2 |
| 行为模型 | 10 + 11 − 2，再把 LSB2 定成 2^1.5 × LSB_total | 19.0 + 1.5 | 2^1.5 | `model/params.py` `LSB2` |

`params.py` 里 `LSB2 = (2**2 * 10 / 2**10) / 2**11 = 19.07 µV`，而 20.5 bit 的总 LSB = 6.744 µV；19.07/6.744 = 2.83 = 2^1.5。也就是说**模型把"8× 平均"提前折进了 LSB2**，再用这个 LSB2 算 SNDR——BL-v3 把这叫"口径混算"，是对的。8× 平均实测只值 +1.71 dB（≈0.28 bit），不是 1.5 bit。

### 1.4 时序三套

| 出处 | ΦC0 | ΦC1 | ΦRA | ΦC2 | guard | 合计 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `README.md` | 7.5 | 15 | 25 | 37.5 | 5 | 90 |
| `interface/ANALOG_DIGITAL_IF.md:55-62` | 10 | 15 | 25 | 40 | — | 90 |
| `spec/ARCH_DECISION_BLv3.md` §4 | 10 | 15 | **20** | **45** | 10 | 100 |
| `digital/DigitalTop.sv:59-64`（实际 RTL） | 0-1 tick=10 ns | 2-4=15 ns | 5-9=25 ns | 10-17=40 ns | 18-19 | 100 |

**RTL 跟的是第二套（25/40），不是"唯一权威" BL-v3 的 20/45。** 数字组按 RTL 做，模拟组按 BL-v3 做，第一次联调就会对不上。

### 1.5 块级一致性：17/23 网表与 spec 不一致

本机 `analog/BLOCK_CONTRACTS.md` 已做过逐块端口抽取（远端没有这份文件）：

- 24 个块目录，23 个有网表；`Dac1_11b/netlist/` 是**空目录**。
- 21 在用 + 3 legacy（`RaMux`、`CmpQ2`、`Dac1_11b`）；`SwSample5v` 标"在用"但 **0 个 X 实例**，从顶层只能追到 20 块。
- **17 个块的 spec 与网表端口不一致**，其中 `Sar1Top`/`SdacPool18`/`CincCouple` 是结构性重写（不是补端口）。
- 24 个块的 `sim/`、`reports/`、`layout/` **全是空目录**；全项目 0 条仿真记录、0 个版图。
- 3 个数字 stub（`SarLogic1_stub`/`SarLogic2_stub`/`DigitalTop_stub`）**subckt 体内没有任何语句** → 顶层所有 `PHI_*`/`SEL`/`ACQ`/`CONV`/`EN` 永远是未驱动网络，`Sar20bTop_tb.scs` 不能跑 tran。

### 1.6 网表里 19 条"跑不了/算错"的硬缺陷（摘 8 条）

| # | 位置 | 现象 | 影响 |
|:--|:---|:---|:---|
| D3 | `Dac2_11b.scs:55-65` | 12 个复位 TG 接 `RST/RSTB`，subckt 无 `RST` 端口 | DAC2 无法复位 |
| D4 | `CincCouple.scs:17` | replica 的 `VREFP/VREFN` 全接 `VCM` | kickback 抵消不成立 |
| D12 | 4 个块 | 电容全部写死 27f…1728f/1.0p，0 个 `unitcap` | 无工艺相关性，失配不可仿真 |
| D13 | `SdacPool18.scs:15-49` | 18 片共用 `D<6:0>`；顶层只接 `D1<6:0>` | 片间 unary 高 3 bit 未实现 |
| D14 | `Sar1Top.scs:7` | `TriLevelBank11` 输出 `SEG<10:0>` 无消费者 | 三电平驱动悬空 |
| D18 | `SdacSlice.scs:31-33,85-91` | 每位底板只有 VREFP/VREFN 两路 TG | DAC1 实际是两电平，不是三电平 |
| D15/D16 | `tb/*.scs` | include 路径实测 MISS；`tb_SdacSlice` 传 20 节点给 14 端口 | 3 个台架 0 个能跑 |
| — | `check_hier.py:68` | 只比 token 数、不展开总线、不查未驱动 | 上面全部"OK 通过" |

`python3 analog/netlist/check_hier.py` 输出 `files=28 subckts=39 instances=220 OK`；`tools/check_consistency.py` 输出 `6 项通过 0 失败`。**这两个 PASS 只证明"文档自洽/符号存在"，不是可仿真证据**——这正是仓库最容易误导人的地方：绿灯很多，但没有一盏是电学的。

### 1.7 远端与本地已经漂移

- 远端缺 `spec/ARCH_DECISION_BLv3.md`、`analog/BLOCK_CONTRACTS.md`、`STATE.md`、`TASKS.md`、`arch/`、`behavioral/`、`tools/`。
- 远端有 `model/results/figures/fig17-20`（洗牌图），但**生成它们需要的 `model/digital_tech.py` 没推**；`model/impairments.py`、`simulate_v2.py` 也没推。
- 结论：远端是"能看不能跑"，本地是"能跑但没版本"。两边都不是可交付状态。

---

## 2. 模拟 CDAC 的结构究竟是什么

### 2.1 先把三个层级分开

"CDAC"在本项目里指三样不同的东西，文档混着叫，必须先拆：

| 名字 | 物理形态 | 干什么 | 网表 |
|:---|:---|:---|:---|
| **DAC1**（一级 CDAC） | 18 片池，每片 3.456 pF，差分 | 采样 VIN + 逐次逼近，产生一级余差 | `SdacSlice.scs` / `SdacPool18.scs` |
| **C_INC**（级间耦合） | 1.0 pF/侧 串联电容 | 把 RA 输出**交流耦合**到 DAC2 顶板，**不采样** | `CincCouple.scs` |
| **DAC2**（二级 CDAC） | 5 bit 主 + 桥 + 6 bit 子，顶板 0.89 pF | 连续时间 SAR：只做电荷减法，不做采样保持 | `Dac2_11b.scs` |

论文的"CT 二级"就是第三行：RA 输出不经过采样开关，直接经 C_INC 加到 DAC2 顶板；比较器连续判决，DAC2 逐位把电荷搬走。这样 RA 的宽带噪声不会被采样折叠回带内，再用 8× LSB 重复把它平均掉（论文摘要：宽带宽 RA 噪声降 7 dB）。

### 2.2 DAC1：网表实际是什么

以 `SdacSlice.scs` 为准（逐行）：

```
C0..C6 = 27f, 54f, 108f, 216f, 432f, 864f, 1728f   // 1C..64C，二进制
Cdum   = 27f                                       // 假电容，补到 128C
合计   = 3456 f = 128 × 27 f                      // 每侧
```

- 采样相（`ACQ=1`）：每位底板经 TG 接 `VIN` → **底板采样**，顶板接比较器输入（高阻）。
- 转换相（`CONV=1`）：每位底板按 `CRi = D<i> & CONV` 接 `VREFP`，`CGi = ~D<i> & CONV` 接 `VREFN` → **两电平**。
- `EN=0`：该片所有底板经 `sw5` 接 `VCM`（备用片/未选中片）。
- 差分：`SdacSlice` = `sdac_half` P 侧 + N 侧，N 侧参考反接（`VREFP↔VREFN`）。
- 8 片顶板经 `SliceMux` 的 TG **硬短接**到 `VSUM_P/N`，送 RA。

**关键事实：8 片拿到的是同一个 `D<6:0>`（`SdacPool18.scs:15-49`），且顶层只把 `D1<6:0>` 接进来（`Sar20bTop.scs:24`）。** 所以：

- 电气上这是 **8 个相同的 7 bit CDAC 并联**，顶板求和 = 平均。分辨率还是 7 bit，只是电容和电荷 ×8（噪声 ÷√8）。
- 文档说的"片间 3 bit unary + 片内 7 bit = 10 bit"**没有任何电路承载**：没有 per-slice 权重、没有 per-slice 码、没有 thermometer 译码。`D1[10:7]` 在顶层被直接丢掉。
- 要变成真的 10 bit，必须二选一：
  (a) **per-slice unary**：8 片做 0..7 的热码，每片内部 7 bit 二进制；顶层要把 `D1[9:7]` 译成 8 个 `EN/ACQ` 或 8 组底板码。这时每片权重相同，靠"几片接 VREFP、几片接 VREFN"实现高 3 位。
  (b) **per-slice 二进制加权**：8 片电容按 1:2:4:… 缩放（1C、2C、4C…），这要求 8 种不同 slice，和"18 片可互换"矛盾，不可取。
  正确做法是 (a)。但 (a) 要求 `EN` 不再只是"接 VCM"，而是"接 VREFP 或 VREFN"；现在的 `EN` 语义（接 VCM）会破坏电荷守恒。

### 2.3 DAC1 的"三电平"为什么没实现

`TriLevelDrv.scs` 确实画了一个三轨驱动（`VREF/VCM/VGND`），`TriLevelBank11` 也例化了 11 个。但：

- 它挂在 `Sar1Top` 里，输出 `SEG<10:0>` **没有任何消费者**（`Sar1Top.scs:7`）。
- `SdacSlice` 的底板开关只有 `VIN`、`VREFP`、`VREFN`、`VCM(EN)` 四路，**没有 `VGND`，也没有 per-bit `VCM`**。
- 所以"三电平"只存在于驱动块的注释里，电容阵列仍是两电平。

这一点很关键：论文用三电平（MSB 回 VCM）来降开关能量和共模扰动，是本项目"低功耗/低失真"的依据之一；网表没实现，就不能拿论文的功耗数字做预算。

### 2.4 DAC1 的 1039 与 28 pF 对不上

- `Dac1_11b/spec.md`：`C_unit=27fF, N_unit=1039` → 1039×27 = 28.05 pF。
- `SdacSlice` 实际：128 单位/片 × 8 片 = 1024 单位 = 27.65 pF。
- 差 15 个单位（405 fF）。这 15 个单位**没有任何网表或公式解释**；`Dac1_11b/netlist/` 还是空目录。
- README 又写"28 pF/侧/样本（8×3.456 pF）"，而 8×3.456 = 27.65，不是 28。
- 噪声预算按 28 pF 算，实际 27.65 pF 会让 kT/C 噪声高 1.3%（0.06 dB），影响不大，但**口径必须统一**，否则 INL/DR 复算对不上。

### 2.5 DAC2：这个画对了，但位宽标错

`Dac2_11b.scs` 逐行：

```
主阵（VTOP 侧）：432f, 216f, 108f, 54f, 27f, +27f(dum) = 864 f = 32 C_u   → 5 bit
桥：Cbr = 28 f（串在 VTOP 与 SUB 之间）
子阵（SUB 侧）：864f, 432f, 216f, 108f, 54f, 27f, +27f(dum) = 1728 f = 64 C_u → 6 bit
顶板等效：864 + (28 ∥ 1728) ≈ 891.5 f ≈ 0.89 pF
```

- 5 + 6 = **11 bit**，不是 12 bit。目录名 `Dac2_11b` 和网表一致；`blocks/Dac2_11b/spec.md` 标题写 `Dac2_12b`、端口 `DIN<11:0>`、"12 bit" 是旧稿；`Sar2Ct/spec.md` 也写 12b。**数字组如果按 12b 设计，会多一位。**
- 桥比：β = 28/(28+1728) = 1/62.7，理想 1/64；偏 +2.1%，子阵 LSB 略大，属于安全侧（单调、可校准）。**不是"错 2×"**，不需要把 28 f 改成 55.7 f（那会掉到 10 bit）。
- 复位：12 个 `tg18` 栅极接 `RST/RSTB`，但 subckt 端口表里没有 `RST` → 悬空。DAC2 现在**不能复位**，仿真一上电就是浮空顶板。
- 顶板直接送 `Cmp2`，没有采样开关；C_INC 1.0 pF 把 RA 输出耦合过来。这就是"CT 二级"的电路形态。

### 2.6 C_INC 与 replica

- `CincCouple.scs:9-10`：`Cip/Cin = 1.0 pF` 理想电容。spec 建议 864 fF（32×27），网表用 1000 fF，差 +15.7%，且 1000/27 = 37.04 不是整数单位。
- replica：`Xrep (D2 ... VCM VCM VCM VREPP)` —— **参考全接 VCM**，`Crep/Cren` 都从 `VREPP` 到 `VOUTP/VOUTN`。这样 replica 输出没有信号，注入的是共模，**kickback 抵消完全不成立**（D4）。
- 正确接法应该是 replica 的 `VREFP/VREFN` 接与主 DAC2 相同的参考，`Crep` 交叉接到**反相**顶板（或用反相器），并且 replica 的顶板要接到一个低阻节点（不是 VCM 直连）。

### 2.7 一句话回答"CDAC 结构究竟是什么"

> **网表层面**：DAC1 = 18 片池、每片 128×27 fF 的 7 bit 二进制、底板采样、两电平切换、8 片顶板硬短接求和（有效 7 bit ×8 并联）；DAC2 = 5 bit 主阵 + 28 fF 串联桥 + 6 bit 子阵的 11 bit 分段 CDAC，顶板经 1 pF C_INC 交流耦合到 RA，无采样开关（CT）；replica 画了但接错。
> **文档层面**：DAC1 应是 3 bit unary（片间）+ 7 bit binary（片内）= 10 bit、三电平；DAC2 应是 12 bit。**两者都没在网表里兑现。**

---

## 3. 数字那边究竟需要知道什么

数字组不是"要一份端口表"，而是要**六个包子**。下面每项给"为什么需要 / 仓库现状 / 建议"。

### 3.1 几何与权重包（没有这个，重构公式写不出来）

| 项 | 为什么数字要知道 | 仓库现状 | 建议 |
|:---|:---|:---|:---|
| 一级分段方式：3 unary + 7 binary 还是 10 binary | 决定 mapper 是热码译码还是二进制 | 文档说 3+7，网表是 7（无 unary） | 先定 (a) 方案，再给 `D1[9:0]` 的位定义 |
| 每片权重（单位数、C_u、失配 σ） | 校准系数按片/按单位组织 | 只有 `3.456 pF`，无 per-slice 表 | 出 18×128 的权重表 CSV |
| 桥比 β、主/子阵单位数 | 决定 `D2` 的位权与冗余 | 28 fF/864 fF/1728 fF 有，β 没写 | 给 β=1/62.7 与校准后的名义值 |
| 冗余 R（±2 还是 ±2.5 LSB1） | 决定 ADC2 窗口、溢出判决、码合并 | 三套口径：2.5 / 2 / 2 | 冻结一个，写进接口 |
| LSB1/LSB2/LSB_total、FS、G | 所有定点缩放 | 三套（9.766 mV/19.07 µV/6.744 µV vs 2.441 mV/…） | 用 BL-v3 一套，出换算表 |
| 输出码宽/偏置/饱和 | FramePack 与 LVDS | `DOUT<21:0>` 22 bit、中心 0x200000 | 明确 20.0 bit 还是 20.5 bit |

### 3.2 开关真值表包（没有这个，SAR 控制器写不对）

数字必须知道每个相位下每个底板开关的**唯一合法状态**：

| 相位 | 采样开关 | 底板（每片每位） | 顶板 | EN |
|:---|:---|:---|:---|:---|
| ACQ | 闭合 | 全部接 VIN | 高阻/复位 | 1 |
| C0/C1 | 断开（先断后合） | 按 `D1` 接 VREFP 或 VREFN（**或 VCM，若三电平**） | 送 Cmp1 | 1 |
| RA | 断开 | 保持 | 送 RA | 1 |
| C2 | 断开 | DAC2 按 `D2` 接 VREFP2/VREFN2 | Cmp2 | — |
| IDLE | 断开 | 全部接 VCM | 高阻 | 0 |

现状：`SdacSlice` 只有两电平；`EN=0→VCM` 的语义与"unary 选片"冲突；三电平无落点。**数字组拿不到"VCM 那一位到底谁说了算"的答案。**

### 3.3 切片池包（没有这个，调度器就是空转）

| 项 | 现状 | 缺口 |
|:---|:---|:---|
| 池容量 18、每帧 8 转换 + 8 采样 + 2 备 | 有 | — |
| 角色交换周期 100 ns | 有 | — |
| `ELIGIBLE[17:0]` 语义（复位完成后置位） | 接口文档有 | 模拟侧没实现（无复位完成信号） |
| `SLICE_ID` 冻结（一笔内不变） | 接口文档有 | RTL 的 `SliceSched` 是固定轮换，无 ID 冻结、无 stall |
| 因果性：转换组必须是上一帧的采样组 | `SliceSched` 满足（conv=上一 acq） | 但 `shuffle=True` 的随机版在模型里 `conv[n]≠acq[n-1]`（参考仓库自己登记 0/8191） |
| 备用片怎么用（替坏片还是打散杂散） | 未定 | 决定 `STALL` 策略与良率重映射 |

### 3.4 判决/握手包（没有这个，ΦC2 做不出来）

| 信号 | 数字需要知道 | 现状 |
|:---|:---|:---|
| `CMP1/2_CLK` 与判决延迟 | ≤1.2 ns / 2 ns 一拍 | 只有文字，无 `READY` |
| `CMP*_READY`（4 相握手） | 决定能否异步等待 | **完全没有**（`Cmp1/Cmp2` 无此端口；RTL 无握手） |
| 输出极性/保持时间 | 高有效、保持到下一 CLK | 假设，未签 |
| 亚稳态处理 | 超时即 cancel 还是重试 | 未定义 |
| 粗量化 15 比较器温度计编码 | `COARSE<14:0>` 的 bubble 合法性 | `sadc_enc` 只做 popcount，不查 bubble |

`ANALOG_DIGITAL_IF.md` 第 9 节自己列了 7 项未决，其中第 3 项就是比较器极性/保持；第 7 项是 `D1_MASK` 位宽位序。**这两项不签，数字 RTL 只能写"假设版"。**

### 3.5 校准/重构包（没有这个，20 bit 是假的）

| 项 | 现状 | 缺口 |
|:---|:---|:---|
| 校准可观测量（每片/每单位能否单独激励） | 无 | 需要 test mode：单 slice 接已知码、单单位切换 |
| 系数格式（48 个系数、位宽、Q 格式） | `ReconWeights.sv` 只有名义 `d1<<12 + (d2−1024)<<3` | 无系数存储、无 SPI 装载、无 LMS |
| 校准在哪做（片外 LMS / 片上） | 注释说"片外训练后 SPI 灌入" | 没有训练脚本/接口 |
| dither 扣除项 | 无 | 重构公式里没有 `−dR` |
| 输出舍入/饱和 | 无 | 22 bit 直接截断 |

### 3.6 DEM/dither 包（没有这个，别写"DEM 有效"）

| 项 | 数字需要知道 | 现状 |
|:---|:---|:---|
| DEM 作用粒度（片级 / 单位级 / 主-子联合） | 决定 mask 生成器复杂度 | 未定；参考仓库只到片级 mask 接口 |
| 可置换单元集合与约束（同权重、同列、同桥） | 决定 permutation 空间 | 未给 |
| dither 位宽/分布/更新率/PRBS 多项式 | 决定 LFSR 与功耗 | 20b10m 写 PRBS31、6 bit/样本、6 步/样本；参考仓库是 32 bit LFSR、8 步抽取、D=2 时 PMF=[1,2,2,2,1]/8 |
| dither 注入点（采样态 / 量化器 / RDAC） | 决定模拟开关与数字扣除 | 接口文档只有 `DITHER[5:0]`，"见 Fig.19 约定"，无定义 |
| dither 幅度（LSB1 为单位）与冗余余量 | 决定会不会溢出 | 无；BL-v3 只剩 2 bit 冗余 |
| 数字扣除公式 | 决定重构 | 无 |

### 3.7 最小接口包（建议直接发给数字组的 10 个文件）

1. `BITMAP.csv`：DAC1 位 → 片 → 单位 → 权重；DAC2 位 → 单位 → 权重；冗余位。
2. `SWITCH_TRUTH.csv`：每相位 × 每开关的合法状态（含三电平、EN、RST）。
3. `SLICE_POOL.csv`：18 片的物理坐标、权重、可用性、角色表。
4. `TIMING.json`：五相位 + 20 子拍的绝对时刻、setup/hold、非重叠。
5. `CMP_IF.md`：CLK/READY/极性/延迟/亚稳态/超时。
6. `CAL_PLAN.md`：可观测量、激励、系数格式、训练位置。
7. `DITHER_SPEC.md`：PRBS、位宽、PMF、注入点、幅度、扣除公式。
8. `RECON_FORMULA.md`：一位一式的定点重构（含 dither 扣除、舍入、饱和）。
9. `FAULT_MAP.md`：RA clip / ADC2 over / ref droop 的 flag 与样本 ID 关联。
10. `EVIDENCE.md`：每条参数的来源（论文/专利/假设）与置信度。

---

## 4. 论文与专利对照

### 4.1 两篇目标论文（已核实公开元数据）

| 项 | CICC 2026（复现目标） | ISSCC 2024 9.8（交织/DEM/dither 来源） |
|:---|:---|:---|
| 标题 | A 3.6mW 5MS/s 100dB-SNDR 2-Step SAR ADC with Continuous-Time Second-Stage and Tracking Averaging | A 9.3nV/rtHz 20b 40MS/s 94.2dB DR Signal-Chain Friendly Precision SAR Converter |
| 作者 | Congyu Jin, Zhaoyang Shen, Xingshuai Zou, Xuanhao Zhang, Han Zhao, Zhong Zhang, Ning Ning, Hongshuai Zhang, Zheng Wang, Zhenbing Li, Shiheng Yang, Xiangyu Mao, Jiaxin Liu | R. Bodnar, H. Kennedy, C. P. Hurrell, A. Ahmad, M. Vickery, L. Smithers, W. Buckley, M. Dutt, P. Delizia, D. Hummerston, P. Czapor（ADI） |
| 会议/DOI | CICC 2026, Seattle, Apr 19-23, pp.1-4, 10.1109/CICC65509.2026.11509489 | ISSCC 2024, pp.182-184, 10.1109/ISSCC49657.2024.10454329 |
| 工艺 | 180 nm CMOS | 40 nm CMOS |
| 关键指标 | 100 dB SNDR @5 MS/s, 3.6 mW, FoM_S 187.8 dB @100 kHz | 20 bit, 40 MS/s, 94.2 dB DR, 9.3 nV/√Hz, 50 mW, FoM_S 180 dB |
| 核心机制 | CT 二级（RA 后不采样，防噪声折叠）+ tracking-averaging LSB repeating（RA 宽带噪声 −7 dB） | 动态交织一级（18 片）、量化器与 RDAC 分离、dither 范围 +2 bit、共享 RA |

**口径提醒**：公开摘要只给"100 dB SNDR / 3.6 mW / FoM 187.8"，**没有给"20.5 bit"**。仓库里的 20.5 bit、SNDR 99.4 dB、DR 102.5 dB、28 pF、G=128、11+12−2.5 都来自对论文正文/讲稿的引用（`bit_allocation.md` 标了 p.36–37、p.41、p.47）。**在这些页码被逐页核对之前，20.5 bit 只能标"仓库转述，待确认"。**

### 4.2 专利（权利要求级）

| 专利 | 标题/受让人 | 与本项目的关系 | 核实程度 |
|:---|:---|:---|:---|
| **US 10,505,561 B2** | Method of applying a dither, and analog to digital converter operating in accordance with the method / Analog Devices Global | **dither 的唯一核心专利**：claim 1 = dither 只加到 sampling DAC 的采样值，**不加到量化器输入**；用与 dither 相关的数字值改写码；claim 2 = 在采样相把 DAC 元件置非零码态实现注入；claim 3 = dither 分配到 slice；claim 5–8 = 第二 dither、分数 dither(<1 LSB)、整数 dither；claim 12 = n bit 拆成 m bit + 其余 | **claim 1–12 已逐条核对**（Google Patents/PatentsDB 全文） |
| **US 10,511,316 B2** | Method of linearizing the transfer characteristic by dynamic element matching / Analog Devices Global | **DEM 的核心专利**：slice 化 + 主/子阵各自轮转 + 二维 shuffle（X 轴共享、列内子位跨 slice），避免大规模 shuffler；明确"主/子边界比例误差 DEM 消不掉" | **摘要与权利要求 1 已核**；逐条未核 |
| US 10,516,408 B2 | Analog to digital converter stage | 量化器与 RDAC 分离、SADC 误差自愈窗口、两条采样通路响应匹配 | 仓库引用，未逐条核 |
| US 10,707,889 B1 | Interleaving method for analog to digital converters | 交织的 tracking 状态更新 | 仓库引用；注意论文 p.3 印成 US10,797,889，疑似笔误 |
| US 10,541,702 B1 | Auxiliary input for ADC input charge | 辅助输入端口/电荷核算 | 仓库引用，未逐条核 |
| US 10,826,519 B1 | Low power reference for an ADC | 低功耗参考 | 仓库引用，未逐条核 |

**专利给出的三个硬约束**（对本项目直接生效）：

1. dither 必须"注入—改码—扣除"三件套齐全（claim 1 + 10/11）。少一件，dither 就变成真误差。
2. dither 可以只加在 DAC 路径、不加在量化器路径（claim 1），这是"不占输入量程"的关键；但要求 DAC 与量化器的采样响应匹配（US10516408B2）。
3. DEM 只对**等权单位的位置置换**有效；桥接电容比例误差是一阶系统误差，**DEM 完全无效**（US10511316B2 的背景与仓库的 12.3 实验都这么说）。所以"上 DEM 就能到 20 bit"是错的，桥比必须校准。

### 4.3 三条路的归属（别把 ADI 的机制算成 CICC 的）

| 机制 | 来自 | 在本项目里的状态 |
|:---|:---|:---|
| CT 二级、8× LSB 重复、tracking averaging | CICC 2026 | 行为模型有（M/ρ），RTL 无（Sinc2 只是 2 点平均） |
| 18 片池、8/8/2 交织、共享 RA | ISSCC 2024 9.8 | 网表/RTL 有骨架，因果性与 stall 未闭合 |
| 量化器/RDAC 分离 | ISSCC 2024 + US10516408 | 未实现（只有一个 Cmp1） |
| DEM（片级/单位级） | ISSCC 2024 + US10511316 | **未实现**（模型/RTL 均零命中） |
| dither（采样态/量化器/RDAC） | US10505561 | **只有字生成，无注入/扣除** |
| 三电平 MSB 切换 | CICC 2026（p.37 只说 MSB） | **未实现**（驱动悬空） |
| 片外 LMS 校准 | 仓库自定（非论文） | 模型有静态校准，RTL 只有名义权重 |

---

## 5. DEM 到底有没有效

### 5.1 本仓库：没有 DEM，所以"有效性"无从谈起

- `model/*.py`：`dither`/`dem` 零命中（26 个文件全查）。
- `digital/*.sv`：`dither`/`dem`/`shuffle` 零命中。
- `SliceSched.sv:3` 自己写："**局限：轮换而非 LFSR/DEM 洗牌；没有 stall/ID 冻结**"。
- 模型里唯一像"洗牌"的是 `interleave.shuffle`：每样本从 18 片里随机抽 8 片，对 8 片的 gain/offset/skew 求平均。这是**切片级误差平均**，不是 CDAC 单位级 DEM。

### 5.2 能跑的"shuffle"收益（我实测复现）

`python3 -m model.experiments`（6 秒，16384 点）：

| 场景 | DR (dB) | SNDR (dB) | SFDR (dBc) |
|:---|:---:|:---:|:---:|
| 10 MS/s shuffle=False | 96.64 | 96.63 | 103.73 |
| 10 MS/s shuffle=True | 95.67 | 95.65 | 124.88 |
| 差值 | **−0.97** | **−0.98** | **+21.15** |

解释：随机选片把固定的片间失配"打散"成每样本的随机误差 → 杂散（SFDR）大幅改善，但总噪声（DR）变差 1 dB。**这是"用 DR 换 SFDR"，不是"DEM 提高线性度"。** 把它写成"DEM 收益 +21 dB"是错的。

### 5.3 参考仓库（ADI 那条路）：只到 mask 接口，没到 DEM

- `docs/digital_status_matrix.md:14` 原文："**默认 dither 与源 3D 单元 DEM 都不启用；源 3D 尚未实现。**"
- `:79`："源 3D DEM 未实现；v1 拒绝单元 DEM。"
- `:46`："不等于源 3D DEM。"
- `dem_usage.json` 显示实际物理单位暴露**不均匀**：子阵单位概率 0.18–0.32（理想 0.25），主阵 bit56 单位 ~0.030–0.033，其它主阵单位 ~0.0136–0.0172（**差 2 倍**）。这不是一个合格的 DEM。
- 仓库自己登记的排列空间是 **64**（`lcm(64,8)`），不是 512；"任何 DEM 收益数字不得引用为专利机制的定量复现"（R16）。

### 5.4 数量级估算（标明是估算，不是实测）

用本仓库静态模型的数字：σu=0.2% 时 DAC1 未校准 INL = **16.4 ppm FS**（`model/experiments` 实测复现）。1 LSB20 = 10 V/2^20 = 9.54 µV = 0.954 ppm FS，所以 16.4 ppm ≈ **17 LSB20**。

- DEM 若能在 N 个状态间均匀随机化，**平均后的 INL** ≈ 16.4/√N ppm：N=64 → 2.05 ppm；N=512 → 0.73 ppm。看起来 512 态够 ±1.5 ppm。
- 但 DEM **不减少单个样本的误差**：每个样本仍然带着当前状态的 ~17 LSB 误差，只是把它变成噪声。8× 重复只能再降 √8 ≈ 2.8 倍 → ~6 LSB。**仍然远大于 1 LSB20。**
- 所以 20 bit 必须靠**校准**（本仓库：16.4 ppm → 0.3 ppm），DEM 只能做"校准后的残余随机化"和"DNL/零宽码修整"。这与仓库自己的结论一致：校准 +7.3 dB，shuffle 只换 SFDR。
- 桥接比例误差（DAC2 的 28 fF ±x%）是**系统误差**，DEM 无效（专利 [11] 明说）。这一项必须靠校准或修调。

**结论**：DEM 在本项目里是"锦上添花的 DNL/杂散工具"，不是"20 bit 的充分条件"；而且现在**一行都没实现**，没有任何可引用的有效性数字。

---

## 6. dither 到底怎么注入，有没有效

### 6.1 三种注入机制（专利 + 仓库实现）

**机制 A：采样态电荷注入（sampling-state charge injection）**

- 做法：采样相把 `2D` 个单位电容的底板从 VIN 改接 `±V_FS`（D 是 dither 幅度，单位为单位电容）。采样电荷里多了一项已知的 `dQ`。
- 优点：不占输入量程（信号路径的衰减是 `(N−2D)/N`，可用同一份 mask 在数字端补偿）；不需要额外的注入电容。
- 专利依据：US10505561B2 **claim 2**（"setting elements of the first sampling DAC to a non-zero code state during acquisition"）。
- 代价：输入增益略降、采样网络失配变大；dither 单元的权重必须校准。
- 仓库实现：`sampling_dither_injection`（参考仓库 `sampler.py`），`D=2` 时 4 个单位；20b10m 只在接口文档写了 `DITHER[5:0]`，**网表没有对应的 dither 单位/开关**。

**机制 B：量化器/RDAC 双端口（dual-port）**

- 做法：`dQ` 加到量化器输入，`dR = 4·dQ` 加到 RDAC 的存储电荷；RDAC 码偏移 `(dR−dQ)/Δ_RDAC`；数字输出减 `dR`。
- 三件套：注入、改码、扣除，缺一不可（US10505561B2 claim 1/10/11；参考仓库 ADR 0009）。
- 优点：量化器看到的是"加了 dither 的输入"，DAC 看到的是"另一个 dither"，两者比例可调（claim 5–8：分数 dither <1 LSB + 整数 dither）。
- 代价：占冗余窗口；`dR` 必须落在 RDAC 的合法码域内，否则溢出（参考仓库 `rdac_over_count`）。

**机制 C：Fig.19 位分裂（bit-split）**

- 做法：一个 6 bit dither 字拆成三段：
  ```
  m = 4·D3 + 2·D2 + D1        // 片内低 3 位，0..7
  L = 2·D5 + m/7              // 低路，分数（<1 LSB1）
  u = 4·D6 + D4               // 高路，整数 LSB1
  k = c − u                   // 实际码域命令
  ```
- 这是专利 US10505561B2 的 Fig.19 七片示例（`source_bound_fig19_evidence.json` 明确写 `source_basis.patent = US10505561B2`，`location = PDF22 Fig.19; PDF33`）。**七片示例不能把 `/7` 改成 `/8` 当八片结论**（参考仓库 task2 README 的警告）。
- 代价：要求 DAC 有"分数码合成"能力（用 slice 异码合成），对 mapper 和校准都是额外负担。

### 6.2 三个机制的"有效性"证据

参考仓库的 `dither_headroom.json` 做的是**余量扫描**（3 模式 × 8 幅度 × 2048 点），不是 INL 扫描。我把它算了出来：

| 模式 | 输入峰值 3.00 V 时 rms 误差 | maxabs | 失效样本 | 数字 clip |
|:---|:---:|:---:|:---:|:---:|
| off | 1.92 µV | 4.00 µV | 0 | 0 |
| sampling | 1.94 µV | 4.42 µV | 0 | 1（高侧） |
| quantizer | **1615 µV** | **22.2 mV** | **38 / 2048** | 0 |

- **sampling dither**：满量程只掉 1 个码、误差 +10%，基本安全。这说明"采样态注入"确实是"不占输入量程"的。
- **quantizer dither**：输入到 2.97 V 还正常，**2.98 V 起开始失效**（5 个样本），3.00 V 时 38/2048 失效、rms 暴涨 800 倍。原因是 dither 把量化器推出阈值/ADC2 窗口。**要让它有效，必须像论文那样把 dither 范围增强 2 bit（多给量化器/ADC2 的窗口），否则最后 ~0.7% 量程不可用。**
- 这份数据**只证明余量代价，不证明线性度收益**。要证明"dither 有效"，必须做 INL/DNL 扫描（开/关 dither 的 INL 峰峰值、DNL 零宽码数），仓库没有这个实验。

### 6.3 一句话回答

> **怎么注入**：三种——采样态把 2D 个单位接 ±V_FS（不占量程）；量化器与 RDAC 双端口按 dQ:dR=1:4 注入并数字扣除；Fig.19 把 6 bit 字拆成 m/L/u 两路分数+整数码。
> **有没有效**：采样态注入在余量上是安全的（满量程只掉 1 码），量化器注入会把最后 ~0.7% 量程打爆（3.0 V 时 38/2048 失效）；线性度收益**没有实验证据**——仓库只做了余量扫描，没做 INL/DNL 对比。
> **是不是 4080 的数字算法**：**不是**。AD4080 的数字子系统是 SINC1/SINC5、sys_error_corr、event_detect、FIFO、SPI、GPIO（`ad4080_dsp/rtl/` 15 个模块），专利复核明确写"这些专利没有一条要求 AD4080 的数字子系统实现 DEM/dither"（`ad4080_dsp/docs/review_round2_patents.md` P-1）。DEM/dither 在 ADC 核内的 DAC 开关驱动与重构里（`rtl/core/dem_addr_gen.sv`、`dither_gen.sv`、`unit_therm.sv` + `src/adi_model/dem.py`、`dither.py`），不在输出 DSP。数字组如果只拿 `ad4080_dsp` 的 spec，永远看不到 DEM/dither。

---

## 7. 我实际跑了什么（可复现）

| 命令 | 结果 | 证据等级 |
|:---|:---|:---:|
| `python3 -m model.selftest` | 4/4 PASS（纯正弦 DR 268 dB、tracking 方差 1.000、CAAZ AZ 抵消 0、静态 INL 0） | L1 |
| `python3 -m model.experiments` | 6 s 完成；复现 README 的 101.87/101.84/130.99、skew 2 ps→98.39、gain 50 ppm→95.97、shuffle 96.64→95.67 / 103.73→124.88、INL 16.4→0.3 ppm | L1 |
| `python3 tools/check_consistency.py` | 6/6 PASS（位账、端口、引脚、文档引用） | L0（文档自洽） |
| `python3 analog/netlist/check_hier.py` | 39 subckt / 220 instance / OK | L0（符号存在） |
| `python3 analog/netlist/check_ports.py` | DigitalTop stub 与 SV 端口 26:26 一致 | L0 |
| 数字 `make lint/sim` | **未跑**：本机无 iverilog/verilator（Windows 主机有 Icarus 12.0，可另跑） | — |
| 模拟前仿 | **跑不了**：`pdk_models.scs` 未填、3 个数字 stub 为空、`Dac2` 无 RST、`CincCouple` replica 接错 | — |

**能复现的**：行为模型的全部动态/静态结论（L1），6 秒，可重复。
**不能复现的**：任何模拟电学结果（L2 及以上）、任何数字 RTL 功能（未跑）、任何版图/后仿（L3+）、任何硅测（L5）。
**最要命的一句**：远端仓库有 69 张 PDF 和 41 张诊断图，但生成 `fig17-20` 的 `digital_tech.py` 没推；**图在、代码不在**，这是"看起来能复现"的最大假象。

---

## 8. 建议的最小重构（不动电路，只动树与口径）

```
20b10m/
├── README.md                 只留：一句话架构 + 一张图 + 三个入口
├── STATUS.md                 唯一状态源（合并 STATE/TASKS/HANDOVER）
├── spec/
│   ├── ARCH.md               唯一架构裁决（BL-v3 或回论文，二选一）
│   ├── BITMAP.csv            位→片→单位→权重（机器可读）
│   ├── TIMING.csv            五相位 + 20 子拍（机器可读）
│   └── EVIDENCE.md           每条参数的来源与等级
├── if/                       给数字组的 10 个文件（见 §3.7）
├── analog/
│   ├── blocks/<B>/{spec.md,netlist,sim,reports,layout}
│   └── legacy/               RaMux / CmpQ2 / Dac1_11b 移出
├── digital/
│   ├── rtl/                  只放可综合的
│   └── tb/
├── model/                    只放能 `python3 -m model.selftest` 跑的
└── review/                   评审与审计（不进交付）
```

三条硬规则：

1. **一个量只有一个文件定义**。位账、相位、G、C_INC 四处引用同一个 CSV/JSON；文档只引用不复制。
2. **spec 与网表不一致时，以网表为准**，spec 必须当轮改齐，否则标 `STALE`（本机 `BLOCK_CONTRACTS.md` C6 已经这么建议）。
3. **每个数字必须带证据标签**：`[论文 p.x]` / `[专利 claim x]` / `[网表 file:line]` / `[假设]`。没有标签的数字不许进 README。

---

## 9. 待确认（不臆造）

| # | 项 | 现状 | 怎么确认 |
|:--|:---|:---|:---|
| 1 | 论文是否真为 20.5 bit | 公开摘要只给 100 dB SNDR | 核对 CICC 2026 正文 p.36–37 |
| 2 | 论文一级是 6+5 还是 4+2+4 | 仓库两说 | 同上 p.37 |
| 3 | 论文三电平用在哪几位 | 仓库说"MSB 若干位" | 同上 p.37 图 |
| 4 | 论文 G 是否 128 | 由 1.7 V 摆幅反推 | 讲稿/正文 |
| 5 | `1039` 单位的来源 | 8×128=1024，多 15 | 问作者或看 DAC1 版图 |
| 6 | DAC2 是 11 还是 12 bit | 网表 11、spec 12 | 以网表为准，改 spec |
| 7 | 比较器 READY 握手 | 完全没有 | 模拟/数字双方签字 |
| 8 | dither 注入点与幅度 | 只有"见 Fig.19" | 定 `DITHER_SPEC.md` |
| 9 | DEM 粒度与 permutation 空间 | 未定 | 先做单位级 mask 原型 |
| 10 | AD4080 数字子系统是否含 DEM/dither | 专利复核说"不含" | 查 AD4080 数据手册 p.54–71 |

---

## 附录 A：关键证据索引

| 结论 | 证据 |
|:---|:---|
| DAC1 每片 128×27 fF、7 bit 二进制 | `analog/blocks/SdacSlice/netlist/SdacSlice.scs:20-27` |
| DAC1 底板两电平 | 同上 `:31-33`（每位只有 VREFP/VREFN 两路 TG） |
| 18 片共用 `D<6:0>` | `analog/blocks/SdacPool18/netlist/SdacPool18.scs:15-49` |
| 顶层丢 `D1[10:7]` | `analog/blocks/Sar20bTop/netlist/Sar20bTop.scs:24` |
| 三电平驱动悬空 | `analog/blocks/Sar1Top/netlist/Sar1Top.scs:7`（`SEG<10:0>` 无消费者） |
| DAC2 5+6、桥 28 fF | `analog/blocks/Dac2_11b/netlist/Dac2_11b.scs:19-54` |
| DAC2 RST 悬空 | 同上 `:55-65` |
| replica 参考接 VCM | `analog/blocks/CincCouple/netlist/CincCouple.scs:17` |
| 数字相位 10/15/25/40 | `digital/DigitalTop.sv:59-64` |
| 调度是固定轮换、无 DEM | `digital/SliceSched.sv:3-6` |
| 重构只有名义权重 | `digital/ReconWeights.sv:23` |
| 接口 dither 无定义 | `interface/ANALOG_DIGITAL_IF.md:91` |
| `D1_MASK` 位宽未定 | 同上 `:88, :153` |
| 模型 LSB2=2^1.5×总 LSB | `model/params.py` 末行 |
| 模型无 DEM/dither | `model/*.py` 全查零命中 |
| shuffle 实测 | `python3 -m model.experiments` 输出 |
| 参考仓库 DEM 未实现 | `docs/digital_status_matrix.md:14,46,79` |
| 参考仓库 DEM 单位暴露不均 | `docs/randomization_caaz/data/dem_usage.json` |
| dither 余量实测 | `docs/readme/data/dither_headroom.json`（24 cells） |
| AD4080 数字不含 DEM/dither | `ad4080_dsp/docs/review_round2_patents.md` P-1 |

## 附录 B：复现命令

```bash
cd /tmp/gh_20bit10m/20b10m
python3 -m model.selftest
python3 -m model.experiments
python3 tools/check_consistency.py            # 本机工作副本才有
python3 analog/netlist/check_hier.py
python3 analog/netlist/check_ports.py
# 数字（需 iverilog）
cd digital && make lint && make sim
```
