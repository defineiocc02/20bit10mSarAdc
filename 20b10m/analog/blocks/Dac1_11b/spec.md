# Dac1_11b

- 层级：L2　父：`Sar1Top`　子：（叶子）
- **V1 基线（单路 5 MS/s），不投产**；V2 交织用 `SdacPool18`。
- 功能：一级 CDAC：1039×27fF，二进制+冗余，三电平切换

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V | 采样期底板接 VIN |  |
| `VINN` | in | analog | 5V |  |  |
| `VREFP` | in | analog | 5V |  |  |
| `VREFN` | in | analog | 5V |  |  |
| `VCM` | in | analog | 5V |  |  |
| `VGND` | in | analog | 5V |  |  |
| `D1<10:0>` | in | digital | 1.8V | 11 bit |  |
| `PHI_S` | in | digital | 5V |  |  |
| `PHI_C1` | in | digital | 5V |  |  |
| `VTOPP` | io | analog | 5V |  |  |
| `VTOPN` | io | analog | 5V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

C_unit=27fF, N_unit=1039, 差分双阵列

## 依赖

（无子模块）

## 待定 / TODO

冗余位与三电平的分界；底板寄生预算

## 验收判据

总容 28pF；权重误差 <0.5 LSB（前仿）；建立 90ns 内到 0.25 LSB1

## 文件位置（预留）

```
blocks/Dac1_11b/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
