# SdacPool18

- 层级：L1　父：`Sar20bTop`　子：`SdacSlice` × 18
- 功能：18 片 DAC1 池：8 转换 + 8 采样 + 2 备用；角色每 100 ns 交换。
- Profile: target。

## 端口（与网表 `SdacPool18.scs` 一致）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` / `VINN` | in | analog | 5V | 差分输入 |  |
| `VREFP` / `VREFN` | in | analog | 5V |  |  |
| `VCM` / `VGND` | in | analog | 5V |  |  |
| `D<55:0>` | in | digital | 1.8V | 8 片 × 7 bit | `bit[7i+6:7i]` = 片 i |
| `ACQ<17:0>` | in | digital | 5V | 采样相 |  |
| `CONV<17:0>` | in | digital | 5V | 转换相 |  |
| `EN<17:0>` | in | digital | 1.8V | 片使能 | 0 = 备用/未选中 |
| `VTOPP<17:0>` / `VTOPN<17:0>` | io | analog | 5V | 各片顶板 | 由 SliceMux 选 8 片 |
| `VDD5` / `GND` | pwr | power | 5V / — |  |  |

## 关键参数

| 项 | 值 | 来源 |
|:---|:---|:---|
| 片数 | 18（8 + 8 + 2） | SSOT #14 |
| 每片 | 128 × 27 fF = 3.456 pF | SSOT #15 |
| 活跃片 | 8 → 27.648 pF/侧 | SSOT #15 |
| 每片码 | 7 bit（127 二进制 + 1 termination） | SSOT #16 |

## 待定 / TODO

- 备用片策略（替坏片 vs 打散杂散）。
- 片间增益失配 <1e-4 的版图约束。
- termination 1C 的接法（OPEN-1）。

## 验收判据

两相位间增益失配 <1e-4；切换无电荷丢失；8 片顶板求和残差 <0.5 LSB1。

## 文件位置

```
blocks/SdacPool18/
├── spec.md          本文件
├── netlist/         SdacPool18.scs
├── sim/
├── reports/
└── layout/
```
