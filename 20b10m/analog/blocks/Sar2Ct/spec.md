# Sar2Ct

- 层级：L1　父：`Sar20bTop`　子：`CincCouple`、`Dac2_12b`、`Dac2Replica`、`Cmp2`、`SarLogic2`
- 功能：二级：CT SAR（C_INC 直连 DAC2，12b，8× LSB 重复）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VRESP` | in | analog | 1.8V | 来自 RA |  |
| `VRESN` | in | analog | 1.8V |  |  |
| `VREFP2` | in | analog | 1.8V |  |  |
| `VREFN2` | in | analog | 1.8V |  |  |
| `VCM` | in | analog | 1.8V |  |  |
| `PHI_RA` | in | digital | 1.8V |  |  |
| `PHI_C2` | in | digital | 1.8V |  |  |
| `D2<11:0>` | out | digital | 1.8V | 12 bit |  |
| `DT<7:0>` | out | digital | 1.8V | 8× 重复码 |  |
| `DONE2` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

C_INC 待定；DAC2 12b；8× 重复约 10ns

## 依赖

CincCouple, Dac2_12b, Dac2Replica, Cmp2, SarLogic2

## 待定 / TODO

C_INC 容值；replica 的匹配要求；重复的时序边界

## 验收判据

kickback 残差<1 LSB2；20 周期在 40ns 内完成

## 文件位置（预留）

```
blocks/Sar2Ct/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
