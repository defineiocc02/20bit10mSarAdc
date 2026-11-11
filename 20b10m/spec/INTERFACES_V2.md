# 接口定义 v2（统一）

> 配套：`spec/interfaces.csv`（机器可读，98 行 = 86 已实现 + 12 待实现）、`spec/ARCH_V2.md`（模块树与位账）
> 校验：`python3 scripts/check_interface.py`（CSV ↔ RTL ↔ analog stub 三方比对）
> 取代：`spec/interfaces.csv`（旧表，21 bit DOUT / D2[11:0] / CLK 5 MHz，全部作废）

---

## 0. 四层接口

| 层 | 边界 | 权威文件 | 数量 | 状态 |
|:---|:---|:---|:---:|:---|
| **L0 芯片引脚** | 封装脚 | `interface/pinout_qfn48.csv` | 48 + EP | 自洽（`scripts/check_pinout.py` OK） |
| **L1 数模接口** | `DigitalTop` ↔ 模拟壳 | 本文件 §2 + CSV 中 `module=DigitalTop` | 26 | 已实现，端口 26/26 与 stub 一致 |
| **L2 数字内部** | 数字叶子模块之间 | 本文件 §3 + CSV 其余模块 | 60 | 已实现（骨架级） |
| **L3 配置/采集** | SPI ↔ 片外 LMS | 本文件 §4 | 12 待实现 | **未实现** |

命名约定：`UPPER_SNAKE` 给跨模块端口，`lower_snake` 给模块内部；低有效信号加 `N` 后缀（`RSTN`、`SAMN`）；位宽一律 `[MSB:LSB]` 显式声明，不允许隐式截断。

---

## 1. 电平、时钟与复位

| 项 | 约定 |
|:---|:---|
| 逻辑电平 | 数字域 1.8 V CMOS；模拟开关控制 5 V（`TriLevelDrv` 抬升） |
| 主时钟 | `CLK200`，200 MHz，占空比 50 %±2 %，抖动 <1 ps（验收） |
| 帧 | 20 tick × 5 ns = 100 ns；`cnt[4:0]` 0–19 |
| 复位 | `RSTN` 低有效；**异步置位、同步释放**；数字域独立 `VDD18D` |
| 跨域 | 只有 `CLK200` 一个时钟域；`CMP*_READY` 为异步输入，需两级同步 + 边沿检测 |
| 相位信号 | `PHI_*` 是**包络**（窗口），不是判决时钟 |

---

## 2. L1：数字 ↔ 模拟（26 端口）

### 2.1 分组

| 组 | 信号 | 方向（相对 DigitalTop） | 说明 |
|:---|:---|:---|:---|
| 时钟复位 | `CLK200`、`RSTN` | in | — |
| 一级码 | `COARSE[14:0]`、`DONE1` | in | 15 cmp 温度计 + 完成 |
| 二级码 | `D2[10:0]`、`DT[7:0]`、`DONE2` | in | 11 bit + 8× 重复 |
| 一级码回读 | `D1[9:0]` | in | **10 有效位**（Arch 修订 D-03：删除第 11 次判决）；当前 RTL 仍为 `D1[10:0]` 且 bit0 恒 0，待数字域收口后统一收窄 |
| 切片控制 | `ACQ[17:0]`、`CONV[17:0]`、`EN[17:0]`、`SEL[17:0]`、`SELB[17:0]` | out | 18 片池 / SliceMux |
| 相位包络 | `PHI_C0`、`PHI_C1`、`PHI_RA`、`PHI_AZ`、`PHI_C2`、`PRE`、`HOLD`、`EN_RA` | out | 5 V 域，经电平抬升 |
| 输出 | `DOUT[21:0]`、`DOUT_RDY`、`MON[7:0]` | out | — |
| 电源 | `VDD18`、`GND` | in | 仅网表 stub 用 |

### 2.2 关键时序（单帧 100 ns）

```
cnt   0    1    2    3    4    5    6    7    8    9   10 ... 17   18   19
ΦC0  ████████
ΦC1            █████████████
ΦRA                          ████████████████████████
ΦC2                                                  ████████████████████████
HOLD  ██                                                              ████████
swap                                                                       ▲
DONE1                  ▲（自定时结束，允许早于包络末）
DONE2                                                        ▲（自定时，超时则 FAULT）
```

| 约束 | 值 | 来源 |
|:---|:---|:---|
| ΦC0 内一级判决数 | 6（4b flash + 2b SAR 中的 2 次） | `Sar1Ctrl` |
| ΦC1 内一级判决数 | 5 | `Sar1Ctrl` |
| ΦC2 内二级判决数 | 19（11 bit + 8 重复） | `ARCH_V2` §5 |
| 单次判决预算 | 一级 ≈1.5–3 ns；二级 ≈2 ns | 假设，待模拟确认（A3） |

### 2.3 握手（自定时）

```
Sar2Ctrl:  phi_c2 ↑ ──► cmp_start ↑ ──► 等 cmp_ready ↑ ──► 采样 cmp2 ──► 下一拍
           phi_c2 ↓ 且 done2 未到 ──► fault ↑（本样本打 flag，不阻塞下一帧）
```

> 现状：RTL 用 `cnt` 直接当判决节拍（一 tick 一判决），与本节不符——这是 D4 的根因，见 `digital/LINT_REPORT.md`。

---

## 3. L2：数字内部模块接口

| 模块 | 输入 | 输出 | 备注 |
|:---|:---|:---|:---|
| `SliceSched` | `clk`、`rstn`、`swap` | `acq[17:0]`、`conv[17:0]`、`en[17:0]`、`sel[17:0]`、`selb[17:0]`、`base[4:0]`、`m_act[3:0]` | 缺有序 `slice_id[4:0]`（planned） |
| `Sar1Ctrl` | `clk`、`rstn`、`coarse[14:0]`、`cmp`、`phi_c0`、`phi_c1` | `d1[10:0]`、`samn[10:0]`、`done1` | 双驱动待修；需 `cmp_ready` |
| `Sar2Ctrl` | `clk`、`rstn`、`cmp2`、`phi_c2` | `d2[10:0]`、`dt[7:0]`、`done2` | 需 `cmp_ready`；`d2[0]` 无赋值 |
| `Sinc2` | `clk`、`rstn`、`d1`、`d2`、`dt`、`valid` | `acc[25:0]`、`acc_valid` | `acc` 未被下游使用（D6） |
| `ReconWeights` | `clk`、`rstn`、`d1`、`d2`、`valid` | `dout[21:0]` | 缺 `CoefReg`/SPI（planned） |
| `FramePack` | `clk`、`rstn`、`din[21:0]`、`valid_in`、`fault` | `dout[23:0]`、`valid_out`、`full` | count 双写（D5） |
| `SerLvds` | `CLK200`、`RSTN`、`DIN[21:0]`、`VALID`、`FAULT`、`SYNC_EN` | `DOUTP/N`、`CLKOUTP/N`、`DRDYP/N` | 未在顶层例化（D2） |

---

## 4. L3：配置与采集（待实现，12 个信号）

| 信号 | 方向 | 宽度 | 用途 | 验收判据 |
|:---|:---|:---:|:---|:---|
| `SPI_SCLK/SDI/SDO/CS` | 双向 | 1 | 4 线 SPI，≤10 MHz | 写 160 槽全读回一致 |
| `CAL_EN` | in | 1 | 校准/采集模式 | 置位后进入采集，普通转换暂停 |
| `CAL_DONE` | out | 1 | 序列完成 | 采集 N 帧后拉高 |
| `TEST_MODE[1:0]` | in | 2 | 测试模式 | 00 正常 / 01 原始码 / 10 斜坡 / 11 保留 |
| `RAW_D1/D2/DT` | out | 11/11/8 | 原始码导出 | 与 `DOUT` 同帧可对齐 |
| `SLICE_ID[4:0]`+`VALID` | out | 6 | 本拍有序起始片号 | 9 次换相覆盖 18 片，重建可复现 |

**系数表（142 个独立系数，160 槽 × 24 bit 预留）**

| 区间 | 槽数 | 内容 |
|:---|:---:|:---|
| 0–125 | 126 | 18 片 × 7 bit 逐片二进制权重 |
| 126–137 | 12 | DAC2 11 位权 + 1 桥接 |
| 138–141 | 4 | 重复增益 / 级间增益 / 失调 / **DAC2 子阵增益**（Cbr=28 fF 比理想 27.0 fF 高 2.08%，导致子阵增益偏差，必须由 1 个系数吸收；与版图 §4.3.1 的硬约束一致） |
| 142–149 | 8 | 粗段系数（**不可省**：参考 droop 残留 21 mV = 2.1 LSB1，码型相关 INL） |
| 150–159 | 10 | 保留（CRC、版本、温度补偿） |

> **18 个片权已删除**（Arch 修订 D-05）：片权与 7×18 位权完全共线（λ 缩放不变），LMS 有 18 个零特征值方向。149 项中 7 个粗段被增益抽头/段间差分吸收 → **142 个独立系数**。

**SPI 帧**：16 bit 地址 + 24 bit 数据；`CS` 下降沿启动，`SCLK` 上升沿采样；读回带 CRC8。

---

## 5. 一致性检查结果

```bash
python3 scripts/check_interface.py     # → CSV ↔ RTL ↔ stub
python3 scripts/check_pinout.py        # → 48 脚编号/分组/必需信号
```

当前（2026-11-08）：RTL 8 模块 / 86 端口；CSV 98 行（86 impl + 12 planned）；stub 26 端口；**三方一致**。
引脚：48 + EP，功能 29 / 电源地 19，**自洽**。

---

## 6. 未定项（阻塞接口冻结）

| # | 问题 | 影响 |
|:--|:---|:---|
| I1 | `CMP1_READY/CMP2_READY` 是否由模拟侧提供（A3） | 自定时无法落地，只能降位或倍频 |
| I2 | 8× 重复在模拟域还是数字域（A2） | `Sinc2` 是累加器还是第二套读出 |
| I3 | 系数 142 的最终表（已定 142，槽位映射待冻结） | SPI 槽位、寄存器面积 |
| I4 | 洗牌是否真做 | 需要 `SLICE_ID` 有序输出（已列 planned） |
