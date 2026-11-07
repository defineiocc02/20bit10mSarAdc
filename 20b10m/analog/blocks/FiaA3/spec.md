# FiaA3

- 层级：L2　父：`RingAmp3`　子：（叶子）
- 功能：输出级偏置 FIA：无需全局 CMFB，大摆幅

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 1.8V |  |  |
| `VINN` | in | analog | 1.8V |  |  |
| `VOUTP` | out | analog | 1.8V |  |  |
| `VOUTN` | out | analog | 1.8V |  |  |
| `VCP` | in | analog | 1.8V |  |  |
| `VCN` | in | analog | 1.8V |  |  |
| `PHI_RA` | in | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

10µA, CL=4pF

## 依赖

（无子模块）

## 待定 / TODO

输出共模设定

## 验收判据

摆幅 1.7V，建立 <20ns

## 文件位置（预留）

```
blocks/FiaA3/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
