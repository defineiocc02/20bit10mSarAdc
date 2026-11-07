# Dac2Replica

- 层级：L2　父：`Sar2Ct`　子：（叶子）
- 功能：DAC2 复刻：只用于 kickback 抵消，不参与量化

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `DIN<11:0>` | in | digital | 1.8V | 与 DAC2 同一码 |  |
| `VREFP` | in | analog | 1.8V |  |  |
| `VREFN` | in | analog | 1.8V |  |  |
| `VCM` | in | analog | 1.8V |  |  |
| `VTOP` | io | analog | 1.8V | 接 RA 输出节点 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

与 DAC2 1:1

## 依赖

（无子模块）

## 待定 / TODO

版图匹配

## 验收判据

与 DAC2 的失配 <1%

## 文件位置（预留）

```
blocks/Dac2Replica/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
