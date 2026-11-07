# Sinc2Dec

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：二阶 CoI（SINC2）+ M 倍抽取

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `DT<7:0>` | in | digital | 1.8V |  |  |
| `CLK` | in | digital | 1.8V |  |  |
| `DO3<23:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

M=8, 位宽≥26

## 依赖

（无子模块）

## 待定 / TODO

进位与溢出

## 验收判据

无溢出，截断噪声 <0.1 LSB

## 文件位置（预留）

```
blocks/Sinc2Dec/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
