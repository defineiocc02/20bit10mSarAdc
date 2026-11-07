# BitRecombine

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：位重组：D1(11b) + D2(12b) → 20.5b

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `D1<10:0>` | in | digital | 1.8V |  |  |
| `D2<11:0>` | in | digital | 1.8V |  |  |
| `W2<15:0>` | in | digital | 1.8V | 权重（α 相关） |  |
| `DOUT<20:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

α=2^2.5≈5.66

## 依赖

（无子模块）

## 待定 / TODO

冗余位处理

## 验收判据

无失码，INL 无台阶

## 文件位置（预留）

```
blocks/BitRecombine/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
