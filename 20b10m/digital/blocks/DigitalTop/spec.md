# DigitalTop

- 层级：L1　父：`Sar20bTop`　子：`LsbRepeat8`、`Sinc2Dec`、`GainScale`、`BitRecombine`、`LmsCal`、`SliceShuffler`
- 功能：数字后端：重复码、SINC2、1/G、位重组、LMS

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `D1<10:0>` | in | digital | 1.8V |  |  |
| `D2<11:0>` | in | digital | 1.8V |  |  |
| `DT<7:0>` | in | digital | 1.8V |  |  |
| `CLK` | in | digital | 1.8V |  |  |
| `RSTN` | in | digital | 1.8V |  |  |
| `CAL_EN` | in | digital | 1.8V |  |  |
| `DOUT<20:0>` | out | digital | 1.8V |  |  |
| `RDY` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

M=8, 累加器≥26bit, 1/G 定点

## 依赖

LsbRepeat8, Sinc2Dec, GainScale, BitRecombine, LmsCal

## 待定 / TODO

定点位宽与截断；1/G 的实现

## 验收判据

20.5bit 输出无周期性台阶；SNR 随 M 呈 3dB/倍频

## 文件位置（预留）

```
blocks/DigitalTop/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
