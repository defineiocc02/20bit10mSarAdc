# LsbRepeat8

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：8× LSB 重复码生成（驱动 DAC2 低位）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `DT_IN<7:0>` | in | digital | 1.8V |  |  |
| `PHI_C2` | in | digital | 1.8V |  |  |
| `DT_OUT<7:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

M=8

## 依赖

（无子模块）

## 待定 / TODO

与 SAR2 的接口

## 验收判据

8 拍内完成

## 文件位置（预留）

```
blocks/LsbRepeat8/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
