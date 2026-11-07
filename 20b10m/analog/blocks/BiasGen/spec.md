# BiasGen

- 层级：L1　父：`Sar20bTop`　子：（叶子）
- 功能：偏置与共模产生

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `IREF` | in | analog | 1.8V |  |  |
| `EN` | in | digital | 1.8V |  |  |
| `VBP1` | out | analog | 1.8V |  |  |
| `VBP2` | out | analog | 1.8V |  |  |
| `VBN1` | out | analog | 1.8V |  |  |
| `VBN2` | out | analog | 1.8V |  |  |
| `VCM_OUT` | out | analog | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

总电流 <200µA

## 依赖

（无子模块）

## 待定 / TODO

启动电路

## 验收判据

启动可靠，PVT 下电流变化 <20%

## 文件位置（预留）

```
blocks/BiasGen/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
