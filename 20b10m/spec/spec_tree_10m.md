# 10 MS/s 交付树规格表（spec_tree_10m）

> 用途：把架构冻结值落到交付树每个节点。**块内 `spec.md` 与本表冲突时，以本表为准**（本表是 2026-11-07 10 MS/s 立项后的唯一口径）。
> 证据等级：【论文】原文｜【算术】由论文数字推出｜【估算】工程值｜【待确认】需仿真/作者。

## 0. 顶层

| 项 | 值 | 证据 |
|:---|:---|:---|
| 分辨率 / 速率 | 20.5 bit / **10 MS/s**（2 相 × 5 MS/s，相位差 100 ns） | 【论文】+【算术】 |
| 输入量程 | 差分 **10 Vpp**（每侧 0–5 V） | 【推断·高】 |
| 采样电容 | 28 pF/侧/相（8 片 × 3.456 pF） | 【算术】 |
| 总位数 | 10 + 11 + 1.5(8×) − 2 = 20.5 | 【算术】 |
| 噪声 / DR | 26.5 µVrms / 102.5 dB | 【论文】 |
| SNDR | 100.5@6 k / 99.4@100 k / 95.7@2 M dB | 【论文】 |
| 功耗 | core **≈3.5–3.8 mW**；I/O 12.6–21.6 mW 另计 | 【估算】 |
| 面积 | core **≈0.69 mm²**（MIM 1 fF/µm²）；die **≈1.06 mm² / 36 pad** | 【估算】+ 公开 MIM 密度 |
| 时钟 | 外部 **200 MHz 差分**，无 PLL；σ_t ≤1.0 ps 验收 / 0.5 ps 目标 | 【算术】 |
| 输出 | 22 bit 无符号偏移二进制 @ **400 Mbit/s DDR** + 200 MHz 随路时钟 | 【算术】 |

## 1. 模拟块规格（23 块）

| 块 | 10 MS/s 关键规格 | 验收判据 | 依赖 | 证据 |
|:---|:---|:---|:---|:---|
| `Sar20bTop` | 2×5 MS/s；共享 RA/flash/参考/数字 | 两相输出交错正确；DR ≥102.0 dB（前仿） | 全部 | 【算术】 |
| `SdacPool18` | 18×3.456 pF；A 9（8+1 备）+ B 9（8+1 备） | 片间增益失配 <1e-3（洗牌后等效）；切换无电荷丢失 | SdacSlice | 【算术】 |
| `SdacSlice` | 3.456 pF = 128×27 fF；片内 7 bit 二进制 | 7 bit 单调；0.5 LSB1 建立 ≤1 ns；Ron(MSB) ≤32 Ω | SwSample5v | 【算术】 |
| `SwSample5v` | C_boot 1.7 pF；Ron ≤20 Ω；5 V 厚栅 | ΔRon/Ron ≤0.2%（20 bit 线性度）；电荷注入 <0.1 LSB1 | — | 【估算】 |
| `Dac1_11b` | 兼容包装（内部 = 池） | 端口与池一致 | SdacPool18 | — |
| `Cmp1` | 输入折算噪声 ≤366 µVrms@顶板（11.4 µV 折输入） | 2.36 ns 内出结果；亚稳态 <1e-9 | — | 【算术】 |
| `CmpCoarse4b` + 2b SAR | 15 cmp + 2 步 SAR；6 bit；6.5 ns | 极码不越窗；±0.5 LSB4 = 8 LSB1 ≤ 16 LSB1 窗口 | Cmp1 | 【算术】 |
| `TriLevelDrv` | 三轨 5/2.5/0 V；驱动 74 µm 栅宽 | 死区 ≥0.3 ns；无直通；建立 ≤1 ns | — | 【算术】 |
| `RingAmp3` | 三级；4 pF 负载；1.7 V 摆幅；Zout 300 Ω | 噪声 ≤24.0 µV（平均前）；τ ≤2.3 ns；ΦRA 建立 19 ns | FiaA1/A2/A3 | 【论文】+【算术】 |
| `FiaA1` | AZ 输入级；A1 350 µA | AZ 残差 ≤0.5 LSB1；ΦAZ 早关 ≥2 ns | — | 【估算】 |
| `AmpA2` | diode-load；60 µA | 次极点 ≥500 MHz | — | 【估算】 |
| `FiaA3` | 输出级；10 µA 静态；1.7 V 摆幅 | Zout ≤300 Ω；THD 在 2 MHz ≤−100 dBc | — | 【算术】 |
| `RaMux` | A/B 选相 TG；偏斜 ≤50 ps | 切换沿 <200 ps；电荷注入 <0.1 LSB1 | — | 【算术】 |
| `Sar1Top` | 单相比较器 + 驱动 + 逻辑 | ΦC1 15 ns 内 5 bit；ΦC0 7.5 ns 粗量化 | Cmp1/TriLevelDrv | 【算术】 |
| `Sar2Ct` | 11 bit + 8×；ΦC2 27.5 ns | 每位 2.36 ns；M 恒 8；kickback 码相关 ≤61 µV | CincCouple/Dac2 | 【论文】+【算术】 |
| `CincCouple` | C_INC 1 pF/侧；replica 1:1 | 失配 ≤1%；偏斜 ≤50 ps；残差 ≤0.1 LSB2 | Dac2Replica | 【算术】 |
| `Dac2_11b` | 1 pF 等效；5+6 分段；桥 28 fF | 每位建立 ≤0.9 ns；DNL ≤0.5 LSB2 | — | 【算术】+【待确认】 |
| `Dac2Replica` | 与 Dac2 1:1 | 同尺寸/同向/同邻/同开关；偏斜 ≤50 ps | Dac2_11b | 【算术】 |
| `RefBuffer` | 5 V 主 + 2.5 V 副；R_out ≤20 Ω | 噪声 ≤2.9 µV；droop 比较时刻 ≤2.44 mV | — | 【算术】 |
| `DynRefBuf` | 300 pF + 60 pF；R_buf 30–50 Ω | 粗装载 5.5 ns 内补完；无 ringing >0.1 LSB1 | RefBuffer | 【算术】 |
| `BiasGen` | IREF 10 µA；VBP/VBN/VCM | 启动 <10 µs；PVT 下偏置变化 <±15% | — | 【估算】 |
| `CmpQ2` | 第二量化器（暂不实例化） | 同 Cmp1 | — | 【估算】 |

## 2. 每个块必须有的四件套

| 目录 | 内容 | 什么时候必须齐 |
|:---|:---|:---|
| `netlist/` | `.scs` 网表，端口与规格表一致 | **现在（已齐 23 块）** |
| `sim/` | `<run_id>/`：网表快照、log、波形、一行结论 | L1 单元仿真 |
| `reports/` | 单元报告（判据、余量、证据等级） | G2 前 |
| `layout/` | GDS、DRC/LVS、寄生 | G4 前 |

## 3. 与旧 spec 的冲突（以本表为准）

| 旧值 | 新值 | 影响文件 |
|:---|:---|:---|
| 5 MS/s / 5 Vpp / 21 bit / CLK 5 MHz | 10 MS/s / 10 Vpp / 22 bit / CLK 200 MHz | `interface/*`、`spec/bit_allocation.md`、`timing_detail.md` |
| 一级 11 b、G=128、冗余 2.5 b | 一级 10 b、G=32、冗余 2 b | `phase1_arch_budget.md`（部分已改） |
| `Dac2_12b` / 12 bit | `Dac2_11b` / 11 bit | `hierarchy.md`（已改）、`interfaces.csv`（待重导） |
| 单阵列 28 pF | 18 片池 63 pF/侧 | `phase2_layout.md` 面积表需重算 |
