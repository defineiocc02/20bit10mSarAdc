# RefBuffer

- 层级：L1　父：`Sar20bTop`　子：（叶子）
- 功能：参考缓冲（5V 与 1.8V 两套）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VREF_IN` | in | analog | 5V |  |  |
| `VREFP` | out | analog | 5V |  |  |
| `VREFN` | out | analog | 5V |  |  |
| `VREFP2` | out | analog | 1.8V |  |  |
| `VREFN2` | out | analog | 1.8V |  |  |
| `VCM` | out | analog | 5V |  |  |
| `EN` | in | digital | 1.8V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

功耗预算≈980µW

## 依赖

（无子模块）

## 待定 / TODO

稳定性与纹波

## 验收判据

建立到 0.25 LSB1；纹波 <2µV

## 文件位置（预留）

```
blocks/RefBuffer/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
