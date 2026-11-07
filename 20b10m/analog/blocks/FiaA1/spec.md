# FiaA1

- 层级：L2　父：`RingAmp3`　子：（叶子）
- 功能：第一级浮栅反相放大器（FIA）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 1.8V |  |  |
| `VINN` | in | analog | 1.8V |  |  |
| `VOUTP` | out | analog | 1.8V |  |  |
| `VOUTN` | out | analog | 1.8V |  |  |
| `VBP` | in | analog | 1.8V |  |  |
| `VBN` | in | analog | 1.8V |  |  |
| `PHI_AZ` | in | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

350µA

## 依赖

（无子模块）

## 待定 / TODO

AZ 开关与共模

## 验收判据

增益>20dB，带宽>500MHz

## 文件位置（预留）

```
blocks/FiaA1/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
