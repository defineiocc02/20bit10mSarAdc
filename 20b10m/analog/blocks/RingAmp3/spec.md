# RingAmp3

- 层级：L1　父：`Sar20bTop`　子：`FiaA1`、`AmpA2`、`FiaA3`
- 功能：三级 ring amp（A1 FIA / A2 / A3 FIA）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 1.8V | 来自 DAC1 顶板经 864fF |  |
| `VINN` | in | analog | 1.8V |  |  |
| `VOUTP` | out | analog | 1.8V | 驱动 4pF |  |
| `VOUTN` | out | analog | 1.8V |  |  |
| `VCM` | in | analog | 1.8V |  |  |
| `PHI_RA` | in | digital | 1.8V | 放大相 |  |
| `PHI_AZ` | in | digital | 1.8V | auto-zero |  |
| `EN` | in | digital | 1.8V | 采样期断电 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

A1≈350µA, A2≈60µA, A3≈10µA, CL=4pF, 摆幅 1.7V

## 依赖

FiaA1, AmpA2, FiaA3

## 待定 / TODO

FIA 偏置与 AZ 时序；A2 diode-load 的极点

## 验收判据

PHI_RA 内建立到 12bit；摆幅>1.7V；噪声满足 3µV 预算；功耗≈800µW

## 文件位置（预留）

```
blocks/RingAmp3/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
