# Cmp1

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：一级低噪声动态比较器

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V |  |  |
| `VINN` | in | analog | 5V |  |  |
| `CLK` | in | digital | 1.8V |  |  |
| `OUTP` | out | digital | 1.8V |  |  |
| `OUTN` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

输入失调 <1 LSB1（修调后），噪声 <50µV

## 依赖

（无子模块）

## 待定 / TODO

失调修调接口（Vrp/Vrn 或电容修调）

## 验收判据

判决时间 <1.5ns；失调 <1 LSB1

## 文件位置（预留）

```
blocks/Cmp1/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
