# CmpQ2

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：第二量化器：避免转换结束时扰动输入

> **V2（交织）新增模块**，V1 基线不含此模块。

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

与主量化器同构；返回采样 <1ns

## 依赖

（叶子）

## 待定 / TODO

与 Cmp1 的失调匹配

## 验收判据

转换结束对输入的扰动 <0.1 LSB

## 文件位置（预留）

```
blocks/CmpQ2/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
