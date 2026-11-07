# AcqTrackCtl

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：采样边沿/回采样边沿/hold-low/tracking 预置控制

> **V2（交织）新增模块**，V1 基线不含此模块。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `CLK` | in | digital | 1.8V |  |  |
| `TP` | out | digital | 5V | 关键下降沿 |  |
| `EN_ACQ<1:0>` | out | digital | 5V | 回采样使能 |  |
| `HOLD<1:0>` | out | digital | 5V | hold-low FET |  |
| `TRACK_VAL<10:0>` | in | digital | 1.8V | 上一相位结果，用于预置 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

TP 与 EN 不重叠；hold-low 保持到转换结束

## 依赖

（叶子）

## 待定 / TODO

TP 抖动预算；预置值的建立时间

## 验收判据

采样边沿抖动 <1ps；预置后输入电流线性

## 文件位置（预留）

```
blocks/AcqTrackCtl/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
