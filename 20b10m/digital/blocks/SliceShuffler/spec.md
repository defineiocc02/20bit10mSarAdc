# SliceShuffler

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：3b round-robin + 二维 unary 洗牌 + dither

> **V2（交织）新增模块**，V1 基线不含此模块。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `IDX<4:0>` | in | digital | 1.8V |  |  |
| `SEED<7:0>` | in | digital | 1.8V |  |  |
| `CAL_EN` | in | digital | 1.8V |  |  |
| `DITHER<1:0>` | in | digital | 1.8V |  |  |
| `SEL<4:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

1ns 内完成；二维（slice × unary）

## 依赖

（叶子）

## 待定 / TODO

组合深度 vs 1ns 预算；是否流水一拍

## 验收判据

18 片使用频次均匀；杂散被摊平到噪底

## 文件位置（预留）

```
blocks/SliceShuffler/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
