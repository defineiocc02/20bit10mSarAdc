# SdacSlice

- 层级：L3　父：`SdacPool18`　子：（叶子）
- 功能：DAC1 的一个 slice（1/8 阵列，3.5 pF），V2 交织用

> **V2（交织）新增模块**，V1 基线不含此模块。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V |  |  |
| `VINN` | in | analog | 5V |  |  |
| `VREFP` | in | analog | 5V |  |  |
| `VREFN` | in | analog | 5V |  |  |
| `VCM` | in | analog | 5V |  |  |
| `VGND` | in | analog | 5V |  |  |
| `DIN<13:0>` | in | digital | 1.8V | slice 内部码 |  |
| `PHI_ACQ` | in | digital | 5V | 采样相 |  |
| `PHI_CONV` | in | digital | 5V | 转换相 |  |
| `VTOPP` | io | analog | 5V |  |  |
| `VTOPN` | io | analog | 5V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

C_slice=3.5pF（28pF/8），单位 27fF

## 依赖

（叶子）

## 待定 / TODO

slice 与整阵列的权重对应；共质心布局约束

## 验收判据

权重误差 <0.5 LSB1；采样带宽 >10×Nyquist

## 文件位置（预留）

```
blocks/SdacSlice/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
