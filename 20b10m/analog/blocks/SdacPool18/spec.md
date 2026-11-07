# SdacPool18

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：18 片 slice 池：8 转换 + 8 采样 + 2 备用（随机化）

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
| `PHI_ACQ<1:0>` | in | digital | 5V | 两相位采样 |  |
| `PHI_CONV<1:0>` | in | digital | 5V | 两相位转换 |  |
| `D1<10:0>` | in | digital | 1.8V |  |  |
| `SLICE_SEL<4:0>` | in | digital | 1.8V | 洗牌结果 |  |
| `VTOPP` | io | analog | 5V |  |  |
| `VTOPN` | io | analog | 5V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

18 片 × 3.5pF = 63pF；8+8 并发

## 依赖

SdacSlice（×18）

## 待定 / TODO

片数（16 还是 18）；备用片的选法

## 验收判据

两相位间增益失配 <1e-4；切换无电荷丢失

## 文件位置（预留）

```
blocks/SdacPool18/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
