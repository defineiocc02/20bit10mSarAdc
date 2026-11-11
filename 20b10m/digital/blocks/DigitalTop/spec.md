# DigitalTop

- 层级：L1　父：`Sar20bTop`　子：`LsbRepeat8`、`Sinc2Dec`、`GainScale`、`BitRecombine`、`LmsCal`、`SliceShuffler`
- 功能：数字后端：相位/调度、D1→D1_MASK mapper + DEM、重复码、SINC2、1/G、位重组、LMS
- Profile: target（SSOT #27–#36）

## 端口（与 `digital/DigitalTop.sv` 一致，27 个）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `D1<9:0>` | in | digital | 1.8V | 一级码 |  |
| `D2<11:0>` | in | digital | 1.8V | 二级码 |  |
| `DT<7:0>` | in | digital | 1.8V | 8× 重复码 |  |
| `D1_MASK<125:0>` | out | digital | 1.8V | 18 片 × 7 bit | 物理掩码 |
| `CLK` / `RSTN` | in | digital | 1.8V | 200 MHz / 低有效 |  |
| `CAL_EN` | in | digital | 1.8V | 校准使能 |  |
| `DOUT<21:0>` | out | digital | 1.8V | 22 bit |  |
| `RDY` | out | digital | 1.8V |  |  |
| `VDD18` / `GND` | pwr | power | 1.8V / — |  |  |

## 关键参数

M=8，累加器 ≥26 bit，1/G 定点；D1 10 bit、D2 12 bit；DEM 8 态片级旋转。

## 依赖

LsbRepeat8, Sinc2Dec, GainScale, BitRecombine, LmsCal

## 待定 / TODO

定点位宽与截断；1/G 的实现；`CMP1/2_READY` 握手（OPEN-4）。

## 验收判据

20.00 bit 输出无周期性台阶；SNR 随 M 呈 3 dB/倍频；`D1_MASK` 名义和 = 128k+b。

## 文件位置

```
blocks/DigitalTop/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
