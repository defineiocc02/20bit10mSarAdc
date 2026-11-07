# Cmp2

- 层级：L2　父：`Sar2Ct`　子：（叶子）
- 功能：二级比较器

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 1.8V |  |  |
| `VINN` | in | analog | 1.8V |  |  |
| `CLK` | in | digital | 1.8V |  |  |
| `OUTP` | out | digital | 1.8V |  |  |
| `OUTN` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

噪声 <50µV

## 依赖

（无子模块）

## 待定 / TODO

失调修调

## 验收判据

判决 <1ns

## 文件位置（预留）

```
blocks/Cmp2/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
