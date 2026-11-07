# CincCouple

- 层级：L2　父：`Sar2Ct`　子：（叶子）
- 功能：C_INC 耦合 + replica 抵消 kickback

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 1.8V | RA 输出 |  |
| `VINN` | in | analog | 1.8V |  |  |
| `VOUTP` | out | analog | 1.8V | DAC2 顶板 |  |
| `VOUTN` | out | analog | 1.8V |  |  |
| `VREPP` | in | analog | 1.8V | replica 用 |  |
| `VREPN` | in | analog | 1.8V |  |  |
| `D2<11:0>` | in | digital | 1.8V | replica 同步驱动 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

C_INC=待定（建议先按 32×27fF=864fF 试）

## 依赖

（无子模块）

## 待定 / TODO

replica 的buffer与开关必须 1:1；版图对称

## 验收判据

顶板扰动 <0.5 LSB2

## 文件位置（预留）

```
blocks/CincCouple/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
