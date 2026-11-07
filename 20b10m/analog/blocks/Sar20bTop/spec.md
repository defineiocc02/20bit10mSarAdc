# Sar20bTop

- 层级：L0　父：`-`　子：`Sar1Top`、`RingAmp3`、`Sar2Ct`、`DigitalTop`、`BiasGen`、`RefBuffer`、`RaMux`、`DynRefBuf`
- 功能：顶层 ADC：20.5 bit / 5 MS/s / 5 Vpp 差分输入

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V | 差分 5Vpp |  |
| `VINN` | in | analog | 5V | 差分 5Vpp |  |
| `VREFP` | in | analog | 5V | 5.0 V |  |
| `VREFN` | in | analog | 5V | 0 V |  |
| `VCM` | in | analog | 5V | 2.5 V |  |
| `CLK` | in | digital | 1.8V | 5 MHz |  |
| `RSTN` | in | digital | 1.8V | 低有效 |  |
| `CAL_EN` | in | digital | 1.8V | 一次性校准使能 |  |
| `DOUT<20:0>` | out | digital | 1.8V | 21 bit | 20.5 bit 补零对齐 |
| `DOUT_RDY` | out | digital | 1.8V |  | 转换完成 |
| `MON<7:0>` | out | analog | 1.8V |  | 测试观测（可删） |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

FS=5Vpp, Fs=5MS/s, 目标 SNDR 99.4dB@100kHz, DR 102.5dB, P<3.6mW

## 依赖

Sar1Top, RingAmp3, Sar2Ct, DigitalTop, BiasGen, RefBuffer

## 待定 / TODO

确定 8 个待定参数；确定电源域划分（5V 输入/1.8V 核心）

## 验收判据

G0：每个端口有范围与时序；G1：整链预算闭合

## 文件位置（预留）

```
blocks/Sar20bTop/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
