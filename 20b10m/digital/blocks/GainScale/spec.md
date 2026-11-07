# GainScale

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：1/G 定点缩放

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `DIN<23:0>` | in | digital | 1.8V |  |  |
| `G_SEL<3:0>` | in | digital | 1.8V |  |  |
| `DOUT<23:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

G 待定

## 依赖

（无子模块）

## 待定 / TODO

与模拟增益的对齐

## 验收判据

缩放误差 <0.05 LSB

## 文件位置（预留）

```
blocks/GainScale/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
