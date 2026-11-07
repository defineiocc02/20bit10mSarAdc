# Sar1Top

- 层级：L1　父：`Sar20bTop`　子：`CoarseAdc6b`、`Dac1_11b`、`SwSample5v`、`Cmp1`、`SarLogic1`、`TriLevelDrv`、`SdacPool18`、`AcqTrackCtl`、`CmpQ2`
- 功能：一级：11b(10+1) DT SAR + 6b 粗量化 + 三电平 DAC1

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V | 差分 |  |
| `VINN` | in | analog | 5V | 差分 |  |
| `VREFP` | in | analog | 5V |  |  |
| `VREFN` | in | analog | 5V |  |  |
| `VGND` | in | analog | 5V |  |  |
| `VCM` | in | analog | 5V | 2.5 V |  |
| `PHI_S` | in | digital | 5V | 采样相 |  |
| `PHI_C0` | in | digital | 5V | 粗量化相 |  |
| `PHI_C1` | in | digital | 5V | 精量化相 |  |
| `PHI_RA` | in | digital | 5V | 余差放大相 |  |
| `D1<10:0>` | out | digital | 1.8V | 11 bit |  |
| `D1_RDY` | out | digital | 1.8V |  |  |
| `VRESP` | out | analog | 1.8V | ±2.83 LSB1 |  |
| `VRESN` | out | analog | 1.8V | ±2.83 LSB1 |  |
| `VTOPP` | io | analog | 5V |  | DAC1 顶板（比较器/RA 共用） |
| `VTOPN` | io | analog | 5V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

CS=28pF(1039×27fF), 三电平(VREF/VCM/VGND), 转换窗 90ns

## 依赖

CoarseAdc6b, Dac1_11b, SwSample5v, Cmp1, SarLogic1, TriLevelDrv

## 待定 / TODO

三电平在 MSB 的分配（哪几位用三电平）；DAC1 冗余位怎么切

## 验收判据

余差在 PHI_RA 结束前建立到 0.5 LSB2；INL<2 LSB（前仿）

## 文件位置（预留）

```
blocks/Sar1Top/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
