# LmsCal

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：一次性 LMS 失配校准

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `ERR<11:0>` | in | digital | 1.8V |  |  |
| `CAL_EN` | in | digital | 1.8V |  |  |
| `COEF<15:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

迭代次数待定

## 依赖

（无子模块）

## 待定 / TODO

校准对象（电容/增益）

## 验收判据

校准后 INL 改善 >2×

## 文件位置（预留）

```
blocks/LmsCal/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
