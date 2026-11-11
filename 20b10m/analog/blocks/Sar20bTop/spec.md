# Sar20bTop

- 层级：L0　父：`-`　子：`SdacPool18`、`SliceMux`、`Sar1Top`、`CmpCoarse4b`、`RingAmp3`、`Sar2Ct`、`DigitalTop`、`BiasGen`、`RefBuffer`、`DynRefBuf`、`ClkRx`
- 功能：20.0 bit / 10 MS/s / 10 Vpp 差分两级 SAR；2 相部分交织（18 片池）。
- Profile: target。

## 端口（与网表 `Sar20bTop.scs` 一致）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` / `VINN` | in | analog | 5V | 差分 10 Vpp | 0–5 V/侧 |
| `VREFP` / `VREFN` | in | analog | 5V | 5.0 / 0 V |  |
| `VREF2` | in | analog | 1.8V | 二级参考 |  |
| `VCM` | in | analog | 5V | 2.5 V |  |
| `CLKP` / `CLKN` | in | digital | 1.8V | 200 MHz 差分 | 无 PLL |
| `RSTN` | in | digital | 1.8V | 低有效 |  |
| `CAL_EN` | in | digital | 1.8V | 一次性校准 |  |
| `IREF` | in | analog | 1.8V | 偏置电流 |  |
| `DOUT<21:0>` | out | digital | 1.8V | 22 bit 偏移二进制 | 中心 2^21 |
| `DOUT_RDY` | out | digital | 1.8V |  |  |
| `MON` | out | analog | 1.8V | 测试观测 |  |
| `VDD5` / `VDD18` / `VDDIO` / `GND` | pwr | power |  |  |  |

## 关键参数

| 项 | 值 | 来源 |
|:---|:---|:---|
| 分辨率 | 20.00 bit（10 + 12 − 2） | SSOT #7 |
| 速率 | 10 MS/s（2 相 × 5 MS/s） | SSOT #10 |
| FS | 10 Vpp 差分 | SSOT #1 |
| 采样电容 | 27.648 pF/侧 | SSOT #15 |
| 帧 / 相位 | 100 ns；10/15/20/45 + 10 guard | SSOT #12 |
| 功耗 / 面积 | core 3.73–4.03 mW / core 0.93 mm² | SSOT #26（估算） |
| 目标 | SNDR 99.4 dB @100 kHz；DR 102.5 dB | 论文转述，待核 |

## 待定 / TODO

- 8 个待定参数（G、C_INC 已定；DAC2 分段、dither、READY 未定）。
- 电源域划分（5 V 输入 / 1.8 V 核心 / VDDIO）。

## 验收判据

G0：每个端口有范围与时序；G1：整链预算闭合。

## 文件位置

```
blocks/Sar20bTop/
├── spec.md          本文件
├── netlist/         Sar20bTop.scs
├── sim/
├── reports/
└── layout/
```
