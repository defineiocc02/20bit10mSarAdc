# SarLogic2

- 层级：L2　父：`Sar2Ct`　子：（叶子）
- 功能：二级 SAR 逻辑 + 8× LSB 重复状态机

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `CMPP` | in | digital | 1.8V |  |  |
| `CMPN` | in | digital | 1.8V |  |  |
| `VALID` | in | digital | 1.8V |  |  |
| `DONE` | out | digital | 1.8V |  |  |
| `P<11:0>` | out | digital | 1.8V |  |  |
| `N<11:0>` | out | digital | 1.8V |  |  |
| `D2<11:0>` | out | digital | 1.8V |  |  |
| `DT<7:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

12 次逼近 + 8 次重复

## 依赖

（无子模块）

## 待定 / TODO

重复期间的 DAC2 码型

## 验收判据

20 周期内完成，无死锁

## 文件位置（预留）

```
blocks/SarLogic2/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
